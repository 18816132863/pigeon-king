from __future__ import annotations

from .side_effect_budget import SideEffectBudget
from .confirmation_ledger import ConfirmationLedger


class ExecutionContract:
    """Contract created before any real-world execution."""

    def build(self, mission: dict, risk_level: str) -> dict:
        budget = SideEffectBudget().resolve(risk_level)
        requires_confirmation = risk_level in {"L3", "L4", "BLOCKED"}
        confirmation = None
        if requires_confirmation:
            confirmation = ConfirmationLedger().require(
                mission.get("mission_id", "unknown"),
                "risk_level_requires_confirmation",
                risk_level,
            )
        return {
            "status": "contract_ready",
            "mission_id": mission.get("mission_id", "unknown"),
            "risk_level": risk_level,
            "side_effect_budget": budget,
            "confirmation": confirmation,
            "audit_required": True,
            "rollback_required": True,
            "verification_required": True,
            "can_execute_without_confirmation": not requires_confirmation,
        }
