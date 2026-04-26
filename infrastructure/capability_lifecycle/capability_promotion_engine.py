from __future__ import annotations

from .capability_maturity_model import CapabilityMaturityModel


class CapabilityPromotionEngine:
    def promote(self, capability: dict) -> dict:
        maturity = CapabilityMaturityModel().classify(capability)
        can_promote = maturity["stage"] in {"experimental", "trusted"} and capability.get("tests_passed", False)
        return {
            "status": "promotion_ready" if can_promote else "stay_current_stage",
            "maturity": maturity,
            "can_be_core": maturity["stage"] == "trusted" and capability.get("user_approved", False),
        }
