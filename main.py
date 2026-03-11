"""Entry point: --serve (FastAPI server) or -p (direct CLI mode)."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

from dotenv import load_dotenv


def _run_server(host: str, port: int) -> None:
    import uvicorn
    from backend.server.app import create_app

    app = create_app()
    uvicorn.run(app, host=host, port=port)


async def _run_cli(prompt: str) -> None:
    from backend.agent.core import AgentCore
    from backend.agent.executor import Executor
    from backend.agent.models import PlanStatus, RiskLevel
    from backend.agent.permissions import PermissionManager
    from backend.agent.planner import Planner
    from backend.llm.factory import create_provider
    from backend.tools.filesystem import (
        CreateDirectoryTool,
        DeleteFileTool,
        EditFileDiffTool,
        ListDirectoryTool,
        ReadFileTool,
        WriteFileTool,
    )
    from backend.tools.registry import ToolRegistry
    from backend.tools.shell import RunCommandTool
    from backend.tools.web_search import WebSearchTool

    import yaml
    from pathlib import Path

    load_dotenv()

    config_path = Path("configs/default.yaml")
    config = yaml.safe_load(config_path.read_text()) if config_path.exists() else {}

    # Tools
    registry = ToolRegistry()
    for tool_cls in [
        ListDirectoryTool, ReadFileTool, WriteFileTool, EditFileDiffTool,
        CreateDirectoryTool, DeleteFileTool, RunCommandTool, WebSearchTool,
    ]:
        registry.register(tool_cls())

    # LLM
    provider_name = config.get("provider", "openrouter")
    model = config.get("model", "anthropic/claude-haiku-4.5")
    providers_config = config.get("providers", {})
    prov_conf = providers_config.get(provider_name, {})
    env_key = prov_conf.get("env_key", "OPENROUTER_API_KEY")
    api_key = os.getenv(env_key, "")
    base_url = prov_conf.get("base_url")
    llm = create_provider(provider_name, api_key, model, base_url)

    # Agent
    async def print_event(event):
        print(f"  [{event['type']}] {json.dumps({k: v for k, v in event.items() if k != 'type'}, default=str)}")

    permission_mgr = PermissionManager(auto_approve=[RiskLevel.LOW])
    planner = Planner(llm=llm, registry=registry)
    executor = Executor(registry=registry, event_callback=print_event)
    agent = AgentCore(
        planner=planner,
        executor=executor,
        permission_manager=permission_mgr,
        event_callback=print_event,
    )

    print(f"\nGenerating plan for: {prompt}\n")
    plan = await agent.handle_request(prompt)

    print(f"Plan ({plan.id}): {plan.status.value}")
    print(f"Reasoning: {plan.reasoning}\n")
    for i, step in enumerate(plan.steps, 1):
        print(f"  {i}. [{step.risk_level.value}] {step.description}")
        print(f"     Tool: {step.tool_name} | Status: {step.status.value}")
        if step.result:
            preview = step.result[:200]
            print(f"     Result: {preview}")
        if step.error:
            print(f"     Error: {step.error}")
        print()

    if plan.status == PlanStatus.AWAITING_APPROVAL:
        answer = input("Approve plan? (y/n): ").strip().lower()
        if answer == "y":
            plan = await agent.approve_plan(plan.id)
            print(f"\nPlan executed: {plan.status.value}")
            for step in plan.steps:
                if step.result:
                    print(f"  {step.description}: {step.result[:200]}")
                if step.error:
                    print(f"  {step.description}: ERROR: {step.error}")
        else:
            await agent.reject_plan(plan.id)
            print("Plan rejected.")


def main():
    parser = argparse.ArgumentParser(description="my_operator — local AI operator")
    parser.add_argument("-p", type=str, help="Prompt for CLI mode")
    parser.add_argument("--serve", action="store_true", help="Start the FastAPI server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.serve:
        _run_server(args.host, args.port)
    elif args.p:
        asyncio.run(_run_cli(args.p))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
