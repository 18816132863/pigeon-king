from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime


@dataclass
class DecisionCycleResult:
    cycle_id: str
    status: str
    observed: dict[str, Any]
    oriented: dict[str, Any]
    decision: dict[str, Any]
    action_plan: list[dict[str, Any]]
    verification_plan: list[dict[str, Any]]
    learning_events: list[dict[str, Any]]
    requires_confirmation: bool
    risk_level: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__


class DecisionCycle:
    """Observe → Orient → Decide → Act-plan → Verify → Learn.

    This is intentionally side-effect-free. It plans and gates actions;
    real execution stays behind route/safety/confirmation policies.
    """

    def run(self, goal: str, context: dict[str, Any] | None = None) -> DecisionCycleResult:
        ctx = context or {}
        observed = {
            "goal": goal,
            "context_keys": sorted(ctx.keys()),
            "signals": ctx.get("signals", []),
        }
        oriented = {
            "intent": "complete_goal",
            "needs_capability_search": any(k in goal for k in ["没技能", "没方案", "搜索", "自动安装", "接入"]),
            "user_style": ctx.get("user_style", "direct_high_autonomy"),
        }
        risk_level = self._classify_risk(goal, oriented)
        requires_confirmation = risk_level in {"L3", "L4", "BLOCKED"}
        decision = {
            "strategy": "bounded_autonomous_execution",
            "risk_level": risk_level,
            "requires_confirmation": requires_confirmation,
            "decision_quality": "rule_checked",
        }
        action_plan = [
            {"step": "compile_goal", "side_effect": False},
            {"step": "select_existing_capability", "side_effect": False},
        ]
        if oriented["needs_capability_search"]:
            action_plan.append({"step": "search_solution_or_capability", "side_effect": False})
            action_plan.append({"step": "build_sandbox_extension_plan", "side_effect": False})
        action_plan.append({"step": "execute_only_after_policy_gate", "side_effect": "depends_on_route"})

        verification_plan = [
            {"check": "route_policy"},
            {"check": "confirmation_gate"},
            {"check": "result_verification"},
            {"check": "rollback_available"},
        ]
        learning_events = [
            {"event": "decision_trace", "write_back": True},
            {"event": "user_preference_signal", "write_back": True},
        ]
        return DecisionCycleResult(
            cycle_id=f"cycle_{abs(hash(goal))}",
            status="planned",
            observed=observed,
            oriented=oriented,
            decision=decision,
            action_plan=action_plan,
            verification_plan=verification_plan,
            learning_events=learning_events,
            requires_confirmation=requires_confirmation,
            risk_level=risk_level,
        )

    def _classify_risk(self, goal: str, oriented: dict[str, Any]) -> str:
        if any(k in goal for k in ["支付", "转账", "删除账号", "绕过确认", "违法"]):
            return "BLOCKED"
        if any(k in goal for k in ["自动安装", "发消息", "打电话", "发布", "删除", "外部接入"]):
            return "L3"
        if oriented.get("needs_capability_search"):
            return "L2"
        return "L1"
