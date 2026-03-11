"""Base LLM provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class LLMResponse(BaseModel):
    content: str = ""
    tool_calls: list[dict[str, Any]] = []
    raw: dict[str, Any] = {}


class BaseLLMProvider(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        ...
