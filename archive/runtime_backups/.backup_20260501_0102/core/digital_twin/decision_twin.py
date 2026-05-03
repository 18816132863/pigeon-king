class DecisionTwin:
    def model(self, decisions: list[dict]) -> dict:
        return {
            "decision_style": "high_autonomy_with_rules",
            "prefers_complete_delivery": any("complete" in str(d) or "一次性" in str(d) for d in decisions),
            "requires_precision": True,
        }
