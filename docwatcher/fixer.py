import re
import requests
import json
from typing import Optional
from docwatcher.config import get_config

FIX_PROMPT = """You are a technical documentation writer.
A piece of documentation has become stale due to a code change.
Your job is to rewrite ONLY the stale section to make it accurate again.

Rules:
- Keep the same tone and style as the original
- Only fix what is actually wrong
- Keep it concise
- Return ONLY the updated documentation text, nothing else
- No explanations, no preamble, just the fixed text"""

def generate_fix(
    old_doc: str,
    reason: str,
    old_code: str,
    new_code: str,
    repo_path: str = '.'
) -> Optional[str]:
    config = get_config(repo_path)
    endpoint = config.get('llm_endpoint', 'http://localhost:1234/v1/chat/completions')
    model = config.get('model', 'auto')

    if model == 'auto':
        base = endpoint.replace('/v1/chat/completions', '')
        try:
            r = requests.get(f"{base}/v1/models", timeout=3)
            data = r.json()
            models = data.get('data') or data.get('models') or []
            if models:
                model = models[0].get('id') or models[0].get('name', 'unknown')
        except Exception:
            model = 'unknown'

    groq_key = __import__('os').environ.get('GROQ_API_KEY', '')
    if groq_key:
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": FIX_PROMPT},
                    {"role": "user", "content": f"""
Old documentation:
{old_doc}

Why it is stale:
{reason}

Old code:
{old_code if old_code else "This is a new function"}

New code:
{new_code}

Write the updated documentation:"""}
                ],
                temperature=0.3,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return None
    else:
        try:
            response = requests.post(
                endpoint,
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": FIX_PROMPT},
                        {"role": "user", "content": f"""
Old documentation:
{old_doc}

Why it is stale:
{reason}

Old code:
{old_code if old_code else "This is a new function"}

New code:
{new_code}

Write the updated documentation:"""}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 300
                },
                timeout=60
            )
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            return None

def apply_fix(file_path: str, old_text: str, new_text: str) -> bool:
    try:
        with open(file_path, 'r', errors='ignore') as f:
            content = f.read()

        if old_text in content:
            updated = content.replace(old_text, new_text, 1)
            with open(file_path, 'w') as f:
                f.write(updated)
            return True

        # old text not found — append as new section instead
        with open(file_path, 'a') as f:
            f.write(f"\n\n{new_text}\n")
        return True

    except Exception as e:
        print(f"apply_fix error: {e}")
        return False