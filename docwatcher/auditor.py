"""
auditor.py
==========
The LLM Audit Engine. Sends (old_code, new_code, doc_snippet) triples to
an LLM (Groq Llama-3-70b preferred, local LM Studio/Ollama fallback) and
parses structured verdicts about documentation staleness.

Resilience features:
  - Exponential backoff with jitter on HTTP 429 / rate-limit errors
  - Daily limit detection: saves progress to audit_progress.json and exits cleanly
  - JSON verdict parsing with regex fallback for malformed responses
"""

import json
import logging
import os
import re
import time
import random
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ---- Prompt Engineering ----
SYSTEM_PROMPT = """You are a senior technical documentation auditor with deep expertise in software engineering.

Given a code change (old vs new implementation) and a documentation snippet, determine whether the documentation is now factually incorrect or misleading.

CRITICAL RULES:
- Only flag "stale: true" when the code's public API, behavior, parameters, return values, or logic changed in a way that directly contradicts what the documentation states.
- Generic docs like "helper utility" or "initializes the component" are almost never stale — do NOT flag them.
- A function rename, parameter addition/removal, or return type change that the docs describe wrongly = stale.
- Implementation detail changes that don't affect documented behavior = NOT stale.
- If unsure, return stale: false. Err heavily on the side of caution.

Respond with ONLY this JSON — no preamble, no explanation, no markdown:
{
  "stale": true or false,
  "severity": "error" or "warning" or "info",
  "reason": "one specific sentence explaining what exactly is outdated"
}

severity guide:
  error   = doc is factually WRONG and will actively mislead a developer
  warning = doc is incomplete or partially outdated but not dangerously wrong
  info    = doc could be more accurate but isn't harmful as-is"""

# Backoff settings
MAX_RETRIES = 5
BASE_DELAY = 1.0      # seconds
MAX_DELAY = 60.0      # seconds
JITTER_RANGE = 0.5    # ±0.5s random jitter

# Progress save file (for daily limit handling)
PROGRESS_FILE = "audit_progress.json"


@dataclass
class LLMVerdict:
    stale: bool
    severity: str        # 'error', 'warning', 'info'
    reason: str
    symbol_name: str
    doc_section: str
    doc_file: str
    doc_line: int


class RateLimitExceeded(Exception):
    """Raised when we hit a hard daily/monthly quota (distinct from a soft 429)."""
    pass


def _build_user_message(symbol_name: str, old_code: str, new_code: str, doc_content: str,
                         doc_file: str, doc_line: int, doc_heading: str) -> str:
    old_display = old_code.strip() if old_code.strip() else "— NEW SYMBOL (did not exist before) —"
    return f"""Symbol changed: `{symbol_name}`

════ OLD CODE ════
{old_display}

════ NEW CODE ════
{new_code.strip()}

════ DOCUMENTATION ════
File: {doc_file}  |  Line: {doc_line}  |  Section: {doc_heading}

{doc_content.strip()}

════════════════
Is the documentation still accurate after this code change?"""


def _parse_verdict(raw: str) -> Optional[dict]:
    """
    Attempt strict JSON parse, then regex fallback.
    Returns None if neither works.
    """
    raw = raw.strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences if present
    cleaned = re.sub(r'```(?:json)?', '', raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Last resort: extract first {...} block
    match = re.search(r'\{[^{}]*\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    logger.warning(f"Could not parse LLM verdict: {raw[:200]}")
    return None


def _exponential_backoff_request(fn, max_retries: int = MAX_RETRIES):
    """
    Call fn() with exponential backoff on rate-limit (429) errors.

    Raises RateLimitExceeded if we get a clear daily quota signal.
    Returns the result of fn() on success, or None after exhausting retries.
    """
    delay = BASE_DELAY
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            err_str = str(e).lower()

            # Hard daily limit signals from Groq
            if any(kw in err_str for kw in ['daily limit', 'monthly limit', 'quota exceeded', 'insufficient_quota']):
                raise RateLimitExceeded(f"Daily/monthly quota hit: {e}")

            # Soft rate limit — back off and retry
            if '429' in err_str or 'rate_limit' in err_str or 'rate limit' in err_str:
                jitter = random.uniform(-JITTER_RANGE, JITTER_RANGE)
                sleep_time = min(delay + jitter, MAX_DELAY)
                logger.warning(f"Rate limited. Backing off {sleep_time:.1f}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(sleep_time)
                delay = min(delay * 2, MAX_DELAY)
                continue

            # Other errors — log and give up for this call
            logger.error(f"LLM call failed (attempt {attempt + 1}): {e}")
            return None

    logger.error(f"Exhausted {max_retries} retries.")
    return None


def _call_groq(messages: list) -> Optional[str]:
    """Call Groq API using the official SDK (Llama-3-70b)."""
    api_key = os.environ.get('GROQ_API_KEY', '')
    if not api_key:
        return None

    try:
        from groq import Groq, RateLimitError
    except ImportError:
        logger.warning("groq SDK not installed. Run: pip install groq")
        return None

    client = Groq(api_key=api_key)

    def _do_call():
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # Best available on Groq free tier
            messages=messages,
            temperature=0.1,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()

    return _exponential_backoff_request(_do_call)


def _call_local(messages: list, repo_path: str = '.') -> Optional[str]:
    """Call a local LLM via LM Studio or Ollama (OpenAI-compatible endpoint)."""
    try:
        from docwatcher.config import get_config
        config = get_config(repo_path)
    except Exception:
        config = {}

    endpoint = config.get('llm_endpoint', 'http://localhost:1234/v1/chat/completions')
    model = config.get('model', 'auto')

    # Auto-detect model name
    if model == 'auto':
        base_url = endpoint.replace('/chat/completions', '').replace('/v1', '')
        try:
            r = requests.get(f"{base_url}/v1/models", timeout=3)
            data = r.json()
            models = data.get('data') or data.get('models') or []
            if models:
                model = models[0].get('id') or models[0].get('name', 'local-model')
        except Exception:
            model = 'local-model'

    def _do_call():
        response = requests.post(
            endpoint,
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 200
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()

    return _exponential_backoff_request(_do_call)


def check_consistency(
    symbol_name: str,
    old_code: str,
    new_code: str,
    doc_content: str,
    doc_file: str = "unknown",
    doc_line: int = 0,
    doc_heading: str = "unknown",
    repo_path: str = '.'
) -> Optional[LLMVerdict]:
    """
    Core audit function. Sends a consistency check to the LLM.

    Returns an LLMVerdict or None if the LLM was unreachable / rate-limited.
    Raises RateLimitExceeded if a hard daily quota is hit (caller should save state).
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": _build_user_message(
            symbol_name, old_code, new_code, doc_content, doc_file, doc_line, doc_heading
        )}
    ]

    # Prefer Groq if key is set, otherwise use local
    groq_key = os.environ.get('GROQ_API_KEY', '')
    if groq_key:
        raw = _call_groq(messages)    # May raise RateLimitExceeded
    else:
        raw = _call_local(messages, repo_path)

    if not raw:
        return None

    verdict_data = _parse_verdict(raw)
    if not verdict_data:
        return None

    return LLMVerdict(
        stale=bool(verdict_data.get("stale", False)),
        severity=verdict_data.get("severity", "info"),
        reason=verdict_data.get("reason", "No reason provided"),
        symbol_name=symbol_name,
        doc_section=doc_heading,
        doc_file=doc_file,
        doc_line=doc_line
    )


def save_progress(results: list, filename: str = PROGRESS_FILE):
    """Persist current audit results to disk before an early exit."""
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Progress saved to {filename} ({len(results)} repos)")
    except Exception as e:
        logger.error(f"Failed to save progress: {e}")


def load_progress(filename: str = PROGRESS_FILE) -> list:
    """Load previously saved audit progress (for resuming interrupted runs)."""
    if not os.path.exists(filename):
        return []
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        logger.info(f"Resumed {len(data)} results from {filename}")
        return data
    except Exception:
        return []
