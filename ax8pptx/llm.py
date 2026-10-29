"""Live LLM call - provider-agnostic, one function.

Reads the key from the environment at call time. Never logs it, never
writes it to disk. Provider selection lives in providers.py.
"""

import json
import os
import urllib.request
import urllib.error
from typing import Optional

from .providers import Provider, resolve


class LLMError(RuntimeError):
    pass


def complete(prompt: str, system: str = "", provider: Optional[Provider] = None,
             model: Optional[str] = None, temperature: float = 0.4,
             max_tokens: int = 8000, timeout: int = 180,
             json_mode: bool = True) -> str:
    """Single non-streaming completion. Returns raw text. Raises LLMError."""
    prov = provider or resolve()
    if prov is None:
        raise LLMError(
            "no provider configured. Set a key for any provider in providers.py "
            "or run: python AX8.py --list-providers")

    key = os.environ.get(prov.key_env, "").strip()
    if prov.needs_key and not key:
        raise LLMError(f"{prov.id}: {prov.key_env} is not set")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    body = {
        "model": model or prov.model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}

    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    # OpenRouter asks for attribution headers; harmless elsewhere
    if prov.id == "openrouter":
        headers["HTTP-Referer"] = "https://github.com/ISI0007/ax8-pptx"
        headers["X-Title"] = "AX8 PPTX"

    req = urllib.request.Request(
        prov.endpoint, data=json.dumps(body).encode("utf-8"),
        method="POST", headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        raise LLMError(f"{prov.id} HTTP {e.code}: {detail}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise LLMError(f"{prov.id} network: {e}") from e

    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise LLMError(f"{prov.id} unexpected response shape: {list(payload)}") from e


def probe(provider: Provider, timeout: int = 20) -> dict:
    """Cheap reachability check - does not spend tokens on most providers.

    Returns {provider, reachable, status, detail}. Never raises.
    """
    import urllib.request as u
    url = provider.endpoint.rsplit("/chat/completions", 1)[0]
    try:
        req = u.Request(url, method="GET",
                        headers={"User-Agent": "AX8-PPTX/0.1"})
        with u.urlopen(req, timeout=timeout) as r:
            return {"provider": provider.id, "reachable": True,
                    "status": r.status, "detail": "ok"}
    except urllib.error.HTTPError as e:
        return {"provider": provider.id, "reachable": True,
                "status": e.code, "detail": "reachable (auth required)"}
    except Exception as e:
        return {"provider": provider.id, "reachable": False,
                "status": None, "detail": f"{type(e).__name__}"}
