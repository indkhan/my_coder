"""Native Anthropic/Claude provider."""

from __future__ import annotations

import json
from typing import Any

import anthropic

from backend.llm.base import BaseLLMProvider, LLMResponse


def _openai_tools_to_anthropic(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert OpenAI tool schemas to Anthropic format."""
    result = []
    for t in tools:
        fn = t["function"]
        result.append({
            "name": fn["name"],
            "description": fn.get("description", ""),
            "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
        })
    return result


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self.model = model
        self.client = anthropic.AsyncAnthropic(api_key=api_key)

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResponse:
        # Extract system message if present
        system = ""
        chat_messages = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                chat_messages.append(m)

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": chat_messages,
            "max_tokens": 4096,
        }
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = _openai_tools_to_anthropic(tools)

        resp = await self.client.messages.create(**kwargs)

        content = ""
        tool_calls_out = []
        for block in resp.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls_out.append({
                    "id": block.id,
                    "function": {
                        "name": block.name,
                        "arguments": json.dumps(block.input),
                    },
                })

        return LLMResponse(
            content=content,
            tool_calls=tool_calls_out,
            raw=resp.model_dump(),
        )
