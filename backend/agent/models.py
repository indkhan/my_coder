"""Data models for the agent orchestration system."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class StepStatus(str, Enum):
    PENDING = "PENDING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PlanStatus(str, Enum):
    DRAFT = "DRAFT"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class PlanStep(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    description: str
    tool_name: str
    tool_args: dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    status: StepStatus = StepStatus.PENDING
    result: str | None = None
    error: str | None = None


class Plan(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    user_request: str
    steps: list[PlanStep] = Field(default_factory=list)
    status: PlanStatus = PlanStatus.DRAFT
    reasoning: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ExecutionResult(BaseModel):
    plan_id: str
    step_id: str
    success: bool
    output: str = ""
    error: str = ""
