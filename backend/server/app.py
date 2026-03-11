"""FastAPI app factory — loads config, wires everything together."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.agent.core import AgentCore
from backend.agent.executor import Executor
from backend.agent.models import RiskLevel
from backend.agent.permissions import PermissionManager
from backend.agent.planner import Planner
from backend.llm.factory import create_provider
from backend.server.routes import _broadcast, router, set_agent
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

_registry: ToolRegistry | None = None


def _load_config() -> dict:
    config_path = Path(__file__).resolve().parents[2] / "configs" / "default.yaml"
    if config_path.exists():
        return yaml.safe_load(config_path.read_text())
    return {}


def create_app() -> FastAPI:
    global _registry

    load_dotenv()
    config = _load_config()

    # --- Tool registry ---
    registry = ToolRegistry()
    registry.register(ListDirectoryTool())
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(EditFileDiffTool())
    registry.register(CreateDirectoryTool())
    registry.register(DeleteFileTool())
    registry.register(RunCommandTool())
    registry.register(WebSearchTool())
    _registry = registry

    # --- LLM provider ---
    provider_name = config.get("provider", "openrouter")
    model = config.get("model", "anthropic/claude-haiku-4.5")

    providers_config = config.get("providers", {})
    prov_conf = providers_config.get(provider_name, {})
    env_key = prov_conf.get("env_key", "OPENROUTER_API_KEY")
    api_key = os.getenv(env_key, "")
    base_url = prov_conf.get("base_url")

    llm = create_provider(provider_name, api_key, model, base_url)

    # --- Agent ---
    risk_policy = config.get("risk_policy", {})
    auto_approve_levels = [
        RiskLevel(r) for r in risk_policy.get("auto_approve", ["LOW"])
    ]

    permission_mgr = PermissionManager(auto_approve=auto_approve_levels)
    planner = Planner(llm=llm, registry=registry)
    executor = Executor(registry=registry, event_callback=_broadcast)
    agent = AgentCore(
        planner=planner,
        executor=executor,
        permission_manager=permission_mgr,
        event_callback=_broadcast,
    )
    set_agent(agent)

    # --- FastAPI ---
    app = FastAPI(title="my_operator", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    return app
