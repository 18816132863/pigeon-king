class SideEffectBudget:
    """Define how much real-world impact is allowed before confirmation."""

    LIMITS = {
        "L0": {"external_write": 0, "device_action": 0, "money": 0},
        "L1": {"external_write": 0, "device_action": 0, "money": 0},
        "L2": {"external_write": 0, "device_action": 0, "money": 0},
        "L3": {"external_write": "confirm_required", "device_action": "confirm_required", "money": 0},
        "L4": {"external_write": "strong_confirm_required", "device_action": "strong_confirm_required", "money": 0},
        "BLOCKED": {"external_write": 0, "device_action": 0, "money": 0},
    }

    def resolve(self, risk_level: str) -> dict:
        return {"risk_level": risk_level, "budget": self.LIMITS.get(risk_level, self.LIMITS["L2"])}
