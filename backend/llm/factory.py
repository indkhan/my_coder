"""LLM provider factory."""

from __future__ import annotations

from backend.llm.base import BaseLLMProvider
from backend.llm.anthropic import AnthropicProvider
from backend.llm.ollama import OllamaProvider
from backend.llm.openai_compat import OpenAICompatProvider

# Known OpenAI-compatible base URLs
_OPENAI_COMPAT_URLS: dict[str, str] = {
    "openrouter": "https://openrouter.ai/api/v1",
    "openai": "https://api.openai.com/v1",
    "groq": "https://api.groq.com/openai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
}


def create_provider(
    provider_name: str,
    api_key: str,
    model: str,
    base_url: str | None = None,
) -> BaseLLMProvider:
    name = provider_name.lower()

    if name in ("anthropic", "claude"):
        return AnthropicProvider(api_key=api_key, model=model)

    if name == "ollama":
        return OllamaProvider(model=model, base_url=base_url)

    if name == "custom":
        if not base_url:
            raise ValueError("base_url required for custom provider")
        return OpenAICompatProvider(api_key=api_key, model=model, base_url=base_url)

    if name in _OPENAI_COMPAT_URLS:
        return OpenAICompatProvider(
            api_key=api_key,
            model=model,
            base_url=base_url or _OPENAI_COMPAT_URLS[name],
        )

    raise ValueError(f"Unknown provider: {provider_name}")
