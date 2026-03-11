"""AgentCore — state machine orchestrator."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from backend.agent.executor import Executor
from backend.agent.models import Plan, PlanStatus, StepStatus
from backend.agent.permissions import PermissionManager
from backend.agent.planner import Planner

EventCallback = Callable[[dict[str, Any]], Awaitable[None]]


async def _noop(event: dict[str, Any]) -> None:
    pass


class AgentCore:
    def __init__(
        self,
        planner: Planner,
        executor: Executor,
        permission_manager: PermissionManager,
        event_callback: EventCallback = _noop,
    ) -> None:
        self.planner = planner
        self.executor = executor
        self.permission_manager = permission_manager
        self.event_callback = event_callback
        self._plans: dict[str, Plan] = {}

    def get_plan(self, plan_id: str) -> Plan | None:
        return self._plans.get(plan_id)

    async def handle_request(self, message: str) -> Plan:
        """Generate a plan for the user's request."""
        plan = await self.planner.generate_plan(message)
        plan = self.permission_manager.flag_plan_for_approval(plan)
        self._plans[plan.id] = plan

        await self.event_callback({
            "type": "plan_generated",
            "plan_id": plan.id,
            "status": plan.status.value,
            "steps": len(plan.steps),
        })

        # If all steps auto-approved, execute immediately
        if plan.status == PlanStatus.APPROVED:
            plan = await self.executor.execute_plan(plan)

        return plan

    async def approve_plan(self, plan_id: str, step_ids: list[str] | None = None) -> Plan:
        """Approve a plan (or specific steps) and execute."""
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")
        if plan.status not in (PlanStatus.AWAITING_APPROVAL, PlanStatus.DRAFT):
            raise ValueError(f"Plan cannot be approved in state: {plan.status}")

        for step in plan.steps:
            if step_ids is None or step.id in step_ids:
                if step.status == StepStatus.AWAITING_APPROVAL:
                    step.status = StepStatus.APPROVED

        plan.status = PlanStatus.APPROVED
        plan = await self.executor.execute_plan(plan)
        return plan

    async def reject_plan(self, plan_id: str) -> Plan:
        """Cancel a plan."""
        plan = self._plans.get(plan_id)
        if not plan:
            raise ValueError(f"Plan not found: {plan_id}")
        plan.status = PlanStatus.CANCELLED
        return plan
