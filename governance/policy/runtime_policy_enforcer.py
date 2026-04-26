from __future__ import annotations


class RuntimePolicyEnforcer:
    """Enforce risk gates for the autonomous runtime loop."""

    def enforce(self, plan: dict) -> dict:
        risk = plan.get("decision_cycle", {}).get("risk_level", "L1")
        if risk == "BLOCKED":
            return {"status": "blocked", "reason": "blocked_risk_level"}
        if risk in {"L3", "L4"}:
            return {"status": "requires_confirmation", "reason": "strong_confirmation_required"}
        return {"status": "allowed", "reason": "within_bounded_autonomy"}
