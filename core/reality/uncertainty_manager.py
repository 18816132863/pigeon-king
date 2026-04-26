from __future__ import annotations


class UncertaintyManager:
    """Do not fake certainty. Route uncertainty to search, probe, or confirmation."""

    def classify(self, reality_state: dict) -> dict:
        missing = reality_state.get("fact_state", {}).get("missing_facts", [])
        stale = reality_state.get("fact_state", {}).get("stale_facts", [])
        if missing:
            action = "resolve_missing_facts"
        elif stale:
            action = "refresh_stale_facts"
        else:
            action = "proceed_to_policy_gate"
        return {
            "status": "classified",
            "uncertainty_level": "high" if missing else "medium" if stale else "low",
            "next_action": action,
            "must_not_claim_success": bool(missing or stale),
        }
