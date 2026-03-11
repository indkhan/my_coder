"""Sequential step executor."""

from __future__ import annotations

import json
from typing import Any, Awaitable, Callable

from backend.agent.models import ExecutionResult, Plan, PlanStatus, PlanStep, StepStatus
from backend.tools.registry import ToolRegistry

EventCallback = Callable[[dict[str, Any]], Awaitable[None]]


async def _noop_callback(event: dict[str, Any]) -> None:
    pass


class Executor:
    def __init__(
        self,
        registry: ToolRegistry,
        event_callback: EventCallback = _noop_callback,
    ) -> None:
        self.registry = registry
        self.event_callback = event_callback

    async def execute_step(self, step: PlanStep) -> ExecutionResult:
        tool = self.registry.get(step.tool_name)
        if not tool:
            step.status = StepStatus.FAILED
            step.error = f"Unknown tool: {step.tool_name}"
            return ExecutionResult(
                plan_id="", step_id=step.id, success=False, error=step.error
            )

        step.status = StepStatus.RUNNING
        await self.event_callback({
            "type": "step_started",
            "step_id": step.id,
            "tool_name": step.tool_name,
            "description": step.description,
        })

        try:
            result = await tool.execute(**step.tool_args)
            if result.success:
                step.status = StepStatus.COMPLETED
                step.result = result.output
                await self.event_callback({
                    "type": "step_completed",
                    "step_id": step.id,
                    "output": result.output[:500],
                })
            else:
                step.status = StepStatus.FAILED
                step.error = result.error
                await self.event_callback({
                    "type": "step_failed",
                    "step_id": step.id,
                    "error": result.error,
                })
            return ExecutionResult(
                plan_id="",
                step_id=step.id,
                success=result.success,
                output=result.output,
                error=result.error,
            )
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            await self.event_callback({
                "type": "step_failed",
                "step_id": step.id,
                "error": str(e),
            })
            return ExecutionResult(
                plan_id="", step_id=step.id, success=False, error=str(e)
            )

    async def execute_plan(self, plan: Plan) -> Plan:
        plan.status = PlanStatus.EXECUTING
        for step in plan.steps:
            if step.status not in (StepStatus.APPROVED, StepStatus.PENDING):
                continue

            result = await self.execute_step(step)
            if not result.success:
                plan.status = PlanStatus.FAILED
                await self.event_callback({
                    "type": "plan_failed",
                    "plan_id": plan.id,
                    "failed_step": step.id,
                    "error": result.error,
                })
                return plan

        plan.status = PlanStatus.COMPLETED
        await self.event_callback({
            "type": "plan_completed",
            "plan_id": plan.id,
        })
        return plan
