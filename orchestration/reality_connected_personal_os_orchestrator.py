from __future__ import annotations

from typing import Any

from core.reality import RealityGroundingKernel
from core.authorization import AuthorizationIntentGateway
from core.project_autonomy import ProjectBrain
from infrastructure.tool_negotiation import ToolCapabilityNegotiator
from infrastructure.execution_runtime import RealExecutionBroker
from infrastructure.upgrade_governance import SelfUpgradeGovernor
from memory_context.learning_loop.audit_replay import AuditReplayLearner


class RealityConnectedPersonalOSOrchestrator:
    """V10.6: bridge strategic autonomy to real-world execution safely."""

    def __init__(self) -> None:
        self.reality = RealityGroundingKernel()
        self.authorization = AuthorizationIntentGateway()
        self.project = ProjectBrain()
        self.tools = ToolCapabilityNegotiator()
        self.execution = RealExecutionBroker()
        self.upgrade = SelfUpgradeGovernor()
        self.audit = AuditReplayLearner()

    def run(self, goal: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        reality = self.reality.ground(goal, context)
        project = self.project.start_project(goal, context.get("events", []))
        tool_negotiation = self.tools.negotiate(
            context.get("required_capability", "search"),
            context.get("available_tools", [{"tool_id": "internal_search", "capabilities": ["search"], "side_effects": []}]),
        )
        action = {
            "action_id": "planned_action",
            "summary": goal,
            "risk_level": "L3" if project["review"]["strong_confirm_required"] else "L2",
            "scopes": context.get("scopes", ["read", "search"]),
            "side_effect": bool(context.get("side_effect", False)),
        }
        auth = self.authorization.gate(action)
        execution = self.execution.prepare(action, auth.get("confirmation_contract"))
        upgrade = self.upgrade.govern("10.5.0", "10.6.0", ["core/reality", "core/authorization", "infrastructure/execution_runtime"])
        audit = self.audit.learn(context.get("traces", [{"action_type": "probe", "outcome": {"status": "ok"}}]))
        return {
            "status": "reality_connected_os_ready",
            "shape": "Reality-Connected Personal OS Agent",
            "reality": reality,
            "project_autonomy": project,
            "tool_negotiation": tool_negotiation,
            "authorization": auth,
            "execution_broker": execution,
            "upgrade_governance": upgrade,
            "audit_replay_learning": audit,
            "real_execution_allowed_now": execution["real_side_effect"] is True,
        }
