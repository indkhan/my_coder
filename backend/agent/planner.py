"""LLM-based plan generator."""

from __future__ import annotations

import json
from typing import Any

from backend.agent.models import Plan, PlanStep, RiskLevel
from backend.llm.base import BaseLLMProvider
from backend.tools.registry import ToolRegistry

SYSTEM_PROMPT = """You are an AI planning assistant. Your job is to create a step-by-step plan to fulfill the user's request.

You have access to the following tools:

{tools_section}

IMPORTANT RULES:
- Output ONLY valid JSON. No markdown, no explanation outside the JSON.
- Do NOT execute anything. Only plan.
- Each step must use exactly one tool from the list above.
- Use the exact tool name and parameter names from the schemas.

Output format:
{{
  "reasoning": "Brief explanation of your approach",
  "steps": [
    {{
      "description": "Human-readable description of what this step does",
      "tool_name": "exact_tool_name",
      "tool_args": {{"param": "value"}}
    }}
  ]
}}"""


def _build_tools_section(registry: ToolRegistry) -> str:
    lines = []
    for tool in registry.list_tools():
        schema = tool.to_openai_schema()["function"]
        lines.append(
            f"- **{tool.name}** (risk: {tool.risk_level.value}): {tool.description}\n"
            f"  Parameters: {json.dumps(schema['parameters'])}"
        )
    return "\n".join(lines)


class Planner:
    def __init__(self, llm: BaseLLMProvider, registry: ToolRegistry) -> None:
        self.llm = llm
        self.registry = registry

    async def generate_plan(self, user_request: str) -> Plan:
        tools_section = _build_tools_section(self.registry)
        system = SYSTEM_PROMPT.format(tools_section=tools_section)

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user_request},
        ]

        resp = await self.llm.chat(
            messages=messages,
            response_format={"type": "json_object"},
        )

        data = json.loads(resp.content)

        steps = []
        for s in data.get("steps", []):
            tool = self.registry.get(s["tool_name"])
            risk = tool.risk_level if tool else RiskLevel.HIGH
            steps.append(
                PlanStep(
                    description=s.get("description", ""),
                    tool_name=s["tool_name"],
                    tool_args=s.get("tool_args", {}),
                    risk_level=risk,
                )
            )

        return Plan(
            user_request=user_request,
            steps=steps,
            reasoning=data.get("reasoning", ""),
        )
