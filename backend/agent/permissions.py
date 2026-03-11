"""Risk-based permission gating."""

from __future__ import annotations

from backend.agent.models import Plan, PlanStatus, PlanStep, RiskLevel, StepStatus


class PermissionManager:
    def __init__(self, auto_approve: list[RiskLevel] | None = None) -> None:
        self.auto_approve = auto_approve or [RiskLevel.LOW]

    def needs_approval(self, step: PlanStep) -> bool:
        return step.risk_level not in self.auto_approve

    def flag_plan_for_approval(self, plan: Plan) -> Plan:
        needs = False
        for step in plan.steps:
            if self.needs_approval(step):
                step.status = StepStatus.AWAITING_APPROVAL
                needs = True
            else:
                step.status = StepStatus.APPROVED
        plan.status = PlanStatus.AWAITING_APPROVAL if needs else PlanStatus.APPROVED
        return plan
