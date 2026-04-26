class CounterfactualReviewer:
    def review(self, selected: dict, alternatives: list[dict]) -> dict:
        safer = [a for a in alternatives if a.get("risk_level", "L1") < selected.get("risk_level", "L1")]
        return {
            "status": "reviewed",
            "selected": selected,
            "safer_alternatives": safer,
            "should_reconsider": bool(safer and selected.get("risk_level") in {"L3", "L4"}),
        }
