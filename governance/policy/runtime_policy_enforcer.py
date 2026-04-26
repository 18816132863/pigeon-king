from __future__ import annotations

from governance.policy.adaptive_execution_policy import select_execution_strategy


class RuntimePolicyEnforcer:
    """Enforce risk gates for the autonomous runtime loop."""

    def enforce(self, plan: dict) -> dict:
        decision_cycle = plan.get("decision_cycle", {})
        risk = decision_cycle.get("risk_level", plan.get("risk_level", "L1"))
        if risk == "BLOCKED":
            return {"status": "blocked", "reason": "blocked_risk_level"}

        strategy = select_execution_strategy(
            capability=plan.get("capability", decision_cycle.get("capability", "unknown")),
            op_name=plan.get("op_name", decision_cycle.get("op_name", "")),
            risk_level=risk,
            adapter_status=plan.get("adapter_status", decision_cycle.get("adapter_status", "probe_only")),
            failure_type=plan.get("failure_type", decision_cycle.get("failure_type")),
            result_uncertain=bool(plan.get("result_uncertain", False)),
            timeout=bool(plan.get("timeout", False)),
        )

        if strategy.mode == "blocked":
            return {"status": "blocked", "reason": strategy.reason, "strategy": strategy.to_dict()}
        if strategy.confirmation_required:
            return {"status": "requires_confirmation", "reason": strategy.reason, "strategy": strategy.to_dict()}
        return {"status": "allowed", "reason": strategy.reason, "strategy": strategy.to_dict()}
