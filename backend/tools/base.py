"""Base tool abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from backend.agent.models import RiskLevel


class ToolResult(BaseModel):
    success: bool
    output: str = ""
    error: str = ""


class BaseTool(ABC):
    name: str
    description: str
    risk_level: RiskLevel
    parameters_schema: dict[str, Any]

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        ...

    def to_openai_schema(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }
