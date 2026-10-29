"""Live LLM call - provider-agnostic, one function.

Reads the key from the environment at call time. Never logs it, never
writes it to disk. If no key is present the caller falls back to canned
JSON so the pipeline stays testable offline.
"""

import json
import os
import urllib.request
import urllib.error
from typing import Optional

DEFAULT_MODEL = "deepseek-chat"
ENDPOINT = "https://api.deepseek.com/chat/completions"


class LLMError(RuntimeError):
    pass


def key_present() -> bool:
    return bool(os.environ.get("DEEPSEEK_API_KEY", "").strip())


def complete(prompt: str, system: str = "", model: str = DEFAULT_MODEL,
             temperature: float = 0.4, max_tokens: int = 8000,
             timeout: int = 180) -> str:
    """Single non-streaming completion. Returns raw text. Raises LLMError."""
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        raise LLMError("DEEPSEEK_API_KEY not set")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = json.dumps({
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {"type": "json_object"},
    }).encode("utf-8")

    req = urllib.request.Request(
        ENDPOINT, data=body, method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        raise LLMError(f"HTTP {e.code}: {detail}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise LLMError(f"network: {e}") from e

    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise LLMError(f"unexpected response shape: {list(payload)}") from e
