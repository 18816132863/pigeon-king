class AutonomyMaturityScore:
    def score(self, capabilities: dict) -> dict:
        dimensions = {
            "decision": bool(capabilities.get("decision")),
            "execution_gate": bool(capabilities.get("execution_gate")),
            "learning": bool(capabilities.get("learning")),
            "privacy": bool(capabilities.get("privacy")),
            "reality_grounding": bool(capabilities.get("reality_grounding")),
            "self_extension": bool(capabilities.get("self_extension")),
        }
        score = int(sum(1 for v in dimensions.values() if v) / len(dimensions) * 100)
        return {"status": "scored", "score": score, "dimensions": dimensions}
