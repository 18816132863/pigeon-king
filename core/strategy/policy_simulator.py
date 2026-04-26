from __future__ import annotations


class PolicySimulator:
    """Simulate whether a plan can pass governance before it reaches execution."""

    def simulate(self, plan: dict) -> dict:
        risk = plan.get("risk_level") or plan.get("evaluation", {}).get("risk_level", "L1")
        if risk == "BLOCKED":
            outcome = "blocked"
        elif risk in {"L3", "L4"}:
            outcome = "strong_confirm_required"
        else:
            outcome = "allowed_under_policy"
        return {
            "status": "simulated",
            "policy_outcome": outcome,
            "requires_confirmation": outcome == "strong_confirm_required",
            "must_have": ["audit", "rollback", "verification"],
        }
