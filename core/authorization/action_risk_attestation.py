class ActionRiskAttestation:
    def attest(self, action: dict) -> dict:
        risk = action.get("risk_level", "L1")
        side_effect = bool(action.get("side_effect", False))
        return {
            "status": "attested",
            "risk_level": risk,
            "side_effect": side_effect,
            "requires_confirmation": risk in {"L3", "L4", "BLOCKED"} or side_effect,
            "human_readable_summary": action.get("summary", action.get("title", "planned action")),
        }
