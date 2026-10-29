"""Provider registry - every endpoint AX8 can talk to.

All entries speak the OpenAI chat-completions wire format, so one client
covers them. Free tiers are marked; paid ones are marked. Adding a provider
is a single dict entry.

Selection order:
  1. --provider flag / AX8_PROVIDER env
  2. first provider whose key is present in the environment
  3. none -> offline fixture
"""

import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Provider:
    id: str
    name: str
    endpoint: str
    model: str
    key_env: str
    tier: str                 # "free" | "freemium" | "paid"
    notes: str = ""
    needs_key: bool = True
    strip_json_fence: bool = True

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def key_present(self) -> bool:
        return bool(os.environ.get(self.key_env, "").strip())

    @property
    def ready(self) -> bool:
        """Usable right now: key present, or no key required at all."""
        return True if not self.needs_key else self.key_present

    def redacted(self) -> dict:
        d = self.to_dict()
        d["key_present"] = self.key_present
        d["ready"] = self.ready
        d["key_env"] = self.key_env
        return d


PROVIDERS: Dict[str, Provider] = {
    # ---------------- free / local ----------------
    "ollama": Provider(
        id="ollama", name="Ollama (local)", tier="free", needs_key=False,
        endpoint="http://localhost:11434/v1/chat/completions",
        model="qwen2.5:14b", key_env="OLLAMA_API_KEY",
        notes="Runs on your machine. Free forever. Needs ollama serve.",
    ),
    "lmstudio": Provider(
        id="lmstudio", name="LM Studio (local)", tier="free", needs_key=False,
        endpoint="http://localhost:1234/v1/chat/completions",
        model="local-model", key_env="LMSTUDIO_API_KEY",
        notes="Local OpenAI-compatible server.",
    ),
    "groq": Provider(
        id="groq", name="Groq", tier="freemium",
        endpoint="https://api.groq.com/openai/v1/chat/completions",
        model="llama-3.3-70b-versatile", key_env="GROQ_API_KEY",
        notes="Free tier with rate limits, very fast inference.",
    ),
    "google": Provider(
        id="google", name="Google AI Studio", tier="freemium",
        endpoint="https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        model="gemini-2.5-flash", key_env="GOOGLE_API_KEY",
        notes="Generous free tier on flash models.",
    ),
    "openrouter": Provider(
        id="openrouter", name="OpenRouter", tier="freemium",
        endpoint="https://openrouter.ai/api/v1/chat/completions",
        model="deepseek/deepseek-chat-v3-0324", key_env="OPENROUTER_API_KEY",
        notes="One key, many models. Some are free (suffix :free).",
    ),
    "cerebras": Provider(
        id="cerebras", name="Cerebras", tier="freemium",
        endpoint="https://api.cerebras.ai/v1/chat/completions",
        model="llama-3.3-70b", key_env="CEREBRAS_API_KEY",
        notes="Free tier, extremely fast.",
    ),
    "mistral": Provider(
        id="mistral", name="Mistral", tier="freemium",
        endpoint="https://api.mistral.ai/v1/chat/completions",
        model="mistral-large-latest", key_env="MISTRAL_API_KEY",
        notes="Free experiment tier.",
    ),
    "together": Provider(
        id="together", name="Together AI", tier="freemium",
        endpoint="https://api.together.xyz/v1/chat/completions",
        model="meta-llama/Llama-3.3-70B-Instruct-Turbo", key_env="TOGETHER_API_KEY",
        notes="Free tier on select models.",
    ),

    # ---------------- paid ----------------
    "deepseek": Provider(
        id="deepseek", name="DeepSeek", tier="paid",
        endpoint="https://api.deepseek.com/chat/completions",
        model="deepseek-chat", key_env="DEEPSEEK_API_KEY",
        notes="Default. Cheap, strong JSON adherence.",
    ),
    "openai": Provider(
        id="openai", name="OpenAI", tier="paid",
        endpoint="https://api.openai.com/v1/chat/completions",
        model="gpt-4o-mini", key_env="OPENAI_API_KEY",
        notes="Baseline quality.",
    ),
    "anthropic": Provider(
        id="anthropic", name="Anthropic", tier="paid",
        endpoint="https://api.anthropic.com/v1/chat/completions",
        model="claude-sonnet-4-20250514", key_env="ANTHROPIC_API_KEY",
        notes="OpenAI-compatible shim endpoint.",
    ),
    "xai": Provider(
        id="xai", name="xAI Grok", tier="paid",
        endpoint="https://api.x.ai/v1/chat/completions",
        model="grok-4", key_env="XAI_API_KEY",
    ),
    "moonshot": Provider(
        id="moonshot", name="Moonshot Kimi", tier="paid",
        endpoint="https://api.moonshot.cn/v1/chat/completions",
        model="kimi-k2-0711-preview", key_env="MOONSHOT_API_KEY",
    ),
    "zhipu": Provider(
        id="zhipu", name="Zhipu GLM", tier="freemium",
        endpoint="https://open.bigmodel.cn/api/paas/v4/chat/completions",
        model="glm-4.5", key_env="ZHIPU_API_KEY",
        notes="Free tier on flash models.",
    ),
    "qwen": Provider(
        id="qwen", name="Alibaba Qwen", tier="freemium",
        endpoint="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        model="qwen-plus", key_env="DASHSCOPE_API_KEY",
    ),
}

CUSTOM = Provider(
    id="custom", name="Custom endpoint", tier="paid",
    endpoint="", model="", key_env="AX8_API_KEY",
    notes="Set AX8_ENDPOINT and AX8_MODEL.",
)


def list_providers(tier: Optional[str] = None) -> List[Provider]:
    out = list(PROVIDERS.values())
    if tier:
        out = [p for p in out if p.tier == tier]
    return sorted(out, key=lambda p: (p.tier != "free", p.id))


def resolve(provider_id: Optional[str] = None) -> Optional[Provider]:
    """Pick a provider: explicit -> env var -> first with a key."""
    if provider_id:
        if provider_id == "custom":
            ep, md = os.environ.get("AX8_ENDPOINT", ""), os.environ.get("AX8_MODEL", "")
            if not ep or not md:
                raise KeyError("custom provider needs AX8_ENDPOINT and AX8_MODEL")
            return Provider(
                id="custom", name="Custom endpoint",
                endpoint=ep, model=md,
                key_env="AX8_API_KEY", tier="paid",
                needs_key=bool(os.environ.get("AX8_API_KEY")),
            )
        if provider_id not in PROVIDERS:
            raise KeyError(
                f"unknown provider {provider_id!r}; try one of {sorted(PROVIDERS)}")
        return PROVIDERS[provider_id]

    env_pick = os.environ.get("AX8_PROVIDER", "").strip()
    if env_pick:
        return resolve(env_pick)

    for p in list_providers():
        if p.ready and p.tier != "free":
            return p
    for p in list_providers("free"):
        if p.id in ("ollama", "lmstudio"):
            return p
    return None


def describe_table() -> str:
    rows = [f"{'ID':<12}{'TIER':<10}{'MODEL':<34}{'KEY ENV':<20}{'KEY':<6}{'READY'}"]
    rows.append("-" * 96)
    for p in list_providers():
        key_col = "none" if not p.needs_key else ("set" if p.key_present else "-")
        rows.append(
            f"{p.id:<12}{p.tier:<10}{p.model[:32]:<34}{p.key_env:<20}{key_col:<6}"
            f"{'yes' if p.ready else 'no'}"
        )
    return "\n".join(rows)
