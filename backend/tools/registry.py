"""Tool registry for discovering and invoking tools."""

from __future__ import annotations

from typing import Any

from backend.tools.base import BaseTool


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def get_openai_schemas(self) -> list[dict[str, Any]]:
        return [t.to_openai_schema() for t in self._tools.values()]

    def get_tool_info(self) -> list[dict[str, str]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "risk_level": t.risk_level.value,
            }
            for t in self._tools.values()
        ]
