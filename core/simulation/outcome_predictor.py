class OutcomePredictor:
    def predict(self, plan: dict) -> dict:
        risk = plan.get("risk_level", "L1")
        probability = {"L0": 0.98, "L1": 0.9, "L2": 0.75, "L3": 0.55, "L4": 0.35, "BLOCKED": 0.0}.get(risk, 0.7)
        return {
            "status": "predicted",
            "success_probability": probability,
            "risk_level": risk,
            "uncertainty": "high" if risk in {"L3", "L4"} else "medium",
        }
