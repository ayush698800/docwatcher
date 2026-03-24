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
    repo_path: str = ".",
) -> Optional[str]:
    config = get_config(repo_path)
    endpoint = config.get("llm_endpoint", "http://localhost:1234/v1/chat/completions")
    model = config.get("model", "auto")

    if model == "auto":
        import requests

        base = endpoint.replace("/v1/chat/completions", "")
        try:
            response = requests.get(f"{base}/v1/models", timeout=3)
            data = response.json()
            models = data.get("data") or data.get("models") or []
            if models:
                model = models[0].get("id") or models[0].get("name", "unknown")
        except Exception:
            model = "unknown"

    user_prompt = f"""
Old documentation:
{old_doc}

Why it is stale:
{reason}

Old code:
{old_code if old_code else "This is a new function"}

New code:
{new_code}

Write the updated documentation:"""

    groq_key = __import__("os").environ.get("GROQ_API_KEY", "")
    if groq_key:
        try:
            from groq import Groq

            client = Groq(api_key=groq_key)
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": FIX_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return None

    try:
        import requests

        response = requests.post(
            endpoint,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": FIX_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 300,
            },
            timeout=60,
        )
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def apply_fix(file_path: str, old_text: str, new_text: str) -> bool:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
            content = handle.read()

        if old_text and old_text in content:
            updated = content.replace(old_text, new_text, 1)
            with open(file_path, "w", encoding="utf-8") as handle:
                handle.write(updated)
            return True

        with open(file_path, "a", encoding="utf-8") as handle:
            handle.write(f"\n\n{new_text}\n")
        return True
    except Exception as exc:
        print(f"apply_fix error: {exc}")
        return False
