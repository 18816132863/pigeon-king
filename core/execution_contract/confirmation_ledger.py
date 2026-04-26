from __future__ import annotations

from datetime import datetime


class ConfirmationLedger:
    """Confirmation ledger contract. Does not fake user confirmation."""

    def require(self, action_id: str, reason: str, risk_level: str) -> dict:
        return {
            "action_id": action_id,
            "status": "confirmation_required",
            "reason": reason,
            "risk_level": risk_level,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "confirmed": False,
        }
