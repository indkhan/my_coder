"""Web search tool using a search API (Serper/Tavily/Brave)."""

from __future__ import annotations

import os
from typing import Any

import httpx

from backend.agent.models import RiskLevel
from backend.tools.base import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    name = "search_web"
    description = "Search the web for information using a search API"
    risk_level = RiskLevel.LOW
    parameters_schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query",
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return (default 5)",
            },
        },
        "required": ["query"],
    }

    async def execute(self, **kwargs: Any) -> ToolResult:
        api_key = os.getenv("SEARCH_API_KEY", "")
        if not api_key:
            return ToolResult(success=False, error="SEARCH_API_KEY not set")

        query = kwargs["query"]
        num_results = kwargs.get("num_results", 5)

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Default to Serper API
                resp = await client.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                    json={"q": query, "num": num_results},
                )
                resp.raise_for_status()
                data = resp.json()

            results = []
            for item in data.get("organic", [])[:num_results]:
                results.append(
                    f"**{item.get('title', '')}**\n{item.get('link', '')}\n{item.get('snippet', '')}"
                )
            output = "\n\n".join(results) if results else "No results found."
            return ToolResult(success=True, output=output)
        except Exception as e:
            return ToolResult(success=False, error=str(e))
