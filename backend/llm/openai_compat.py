"""OpenAI-compatible LLM provider (OpenRouter, OpenAI, Groq, Gemini, custom)."""

from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from backend.llm.base import BaseLLMProvider, LLMResponse


class OpenAICompatProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self.model = model
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
        if response_format:
            kwargs["response_format"] = response_format

        resp = await self.client.chat.completions.create(**kwargs)
        choice = resp.choices[0]
        msg = choice.message

        tool_calls_out = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls_out.append({
                    "id": tc.id,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                })

        return LLMResponse(
            content=msg.content or "",
            tool_calls=tool_calls_out,
            raw=resp.model_dump(),
        )
