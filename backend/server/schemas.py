"""API request/response models."""

from __future__ import annotations

from pydantic import BaseModel


class CommandRequest(BaseModel):
    message: str


class CommandResponse(BaseModel):
    plan_id: str
    status: str
    reasoning: str
    steps: list[dict]


class ApproveRequest(BaseModel):
    step_ids: list[str] | None = None
