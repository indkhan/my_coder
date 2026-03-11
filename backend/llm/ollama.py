"""Ollama local model provider (OpenAI-compatible with extras)."""

from __future__ import annotations

import os
from typing import Any

import httpx

from backend.llm.openai_compat import OpenAICompatProvider


class OllamaProvider(OpenAICompatProvider):
    def __init__(self, model: str, base_url: str | None = None) -> None:
        url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        # Ollama exposes an OpenAI-compatible endpoint at /v1
        super().__init__(api_key="ollama", model=model, base_url=f"{url}/v1")
        self._base = url

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3) as c:
                r = await c.get(f"{self._base}/api/tags")
                return r.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get(f"{self._base}/api/tags")
                r.raise_for_status()
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []
