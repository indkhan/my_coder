"""FastAPI routes — REST + WebSocket."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.agent.core import AgentCore
from backend.server.schemas import ApproveRequest, CommandRequest, CommandResponse

router = APIRouter()

# Will be set by app factory
_agent: AgentCore | None = None
_ws_clients: list[WebSocket] = []


def set_agent(agent: AgentCore) -> None:
    global _agent
    _agent = agent


def _get_agent() -> AgentCore:
    if _agent is None:
        raise RuntimeError("Agent not initialized")
    return _agent


async def _broadcast(event: dict[str, Any]) -> None:
    """Broadcast an event to all connected WebSocket clients."""
    data = json.dumps(event)
    disconnected = []
    for ws in _ws_clients:
        try:
            await ws.send_text(data)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        _ws_clients.remove(ws)


def _plan_to_response(plan: Any) -> CommandResponse:
    return CommandResponse(
        plan_id=plan.id,
        status=plan.status.value,
        reasoning=plan.reasoning,
        steps=[
            {
                "id": s.id,
                "description": s.description,
                "tool_name": s.tool_name,
                "tool_args": s.tool_args,
                "risk_level": s.risk_level.value,
                "status": s.status.value,
                "result": s.result,
                "error": s.error,
            }
            for s in plan.steps
        ],
    )


@router.post("/command", response_model=CommandResponse)
async def submit_command(req: CommandRequest):
    agent = _get_agent()
    plan = await agent.handle_request(req.message)
    return _plan_to_response(plan)


@router.get("/plan/{plan_id}", response_model=CommandResponse)
async def get_plan(plan_id: str):
    agent = _get_agent()
    plan = agent.get_plan(plan_id)
    if not plan:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Plan not found")
    return _plan_to_response(plan)


@router.post("/plan/{plan_id}/approve", response_model=CommandResponse)
async def approve_plan(plan_id: str, req: ApproveRequest | None = None):
    agent = _get_agent()
    step_ids = req.step_ids if req else None
    plan = await agent.approve_plan(plan_id, step_ids)
    return _plan_to_response(plan)


@router.post("/plan/{plan_id}/reject", response_model=CommandResponse)
async def reject_plan(plan_id: str):
    agent = _get_agent()
    plan = await agent.reject_plan(plan_id)
    return _plan_to_response(plan)


@router.get("/tools")
async def list_tools():
    from backend.server.app import _registry
    if _registry:
        return _registry.get_tool_info()
    return []


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    _ws_clients.append(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        _ws_clients.remove(ws)
