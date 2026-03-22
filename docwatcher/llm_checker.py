import json
import requests
from dataclasses import dataclass
from typing import Optional

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL_NAME = "phi-3.5-mini-instruct"

SYSTEM_PROMPT = """You are a documentation accuracy checker.
You will be given a code change (old vs new) and a documentation section.
Your job is to determine if the documentation is still accurate after the code change.

You must respond with ONLY a JSON object in this exact format:
{
  "stale": true or false,
  "severity": "error" or "warning" or "info",
  "reason": "one sentence explanation"
}

Rules:
- stale: true if the doc is now inaccurate or misleading because of the code change
- stale: false if the doc is still accurate or unrelated to the change
- severity error: doc is factually wrong and will mislead developers
- severity warning: doc is partially outdated or incomplete
- severity info: doc could be improved but is not dangerously wrong
- reason: be specific about what exactly is outdated
- respond with JSON only, no extra text"""

@dataclass
class LLMVerdict:
    stale: bool
    severity: str
    reason: str
    symbol_name: str
    doc_section: str
    doc_file: str
    doc_line: int

def check_consistency(
    symbol_name: str,
    old_code: str,
    new_code: str,
    doc_content: str,
    doc_file: str,
    doc_line: int,
    doc_heading: str
) -> Optional[LLMVerdict]:

    old_display = old_code if old_code else "This is a new function — did not exist before"

    user_message = f"""Symbol changed: {symbol_name}

OLD CODE:
{old_display}

NEW CODE:
{new_code}

DOCUMENTATION SECTION (from {doc_file} line {doc_line}, heading: {doc_heading}):
{doc_content}

Is this documentation still accurate after the code change?"""

    try:
        response = requests.post(
            LM_STUDIO_URL,
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.1,
                "max_tokens": 200
            },
            timeout=60
        )

        raw = response.json()["choices"][0]["message"]["content"].strip()

        try:
            verdict_data = json.loads(raw)
        except json.JSONDecodeError:
            import re
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                verdict_data = json.loads(match.group())
            else:
                return None

        return LLMVerdict(
            stale=verdict_data.get("stale", False),
            severity=verdict_data.get("severity", "info"),
            reason=verdict_data.get("reason", "No reason provided"),
            symbol_name=symbol_name,
            doc_section=doc_heading,
            doc_file=doc_file,
            doc_line=doc_line
        )

    except Exception as e:
        return None