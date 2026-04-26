from __future__ import annotations

from datetime import datetime


class UserConfirmationContract:
    """Never fabricate confirmation. Create exact confirmation contract."""

    def create(self, action_id: str, summary: str, risk_level: str, scopes: list[str]) -> dict:
        return {
            "confirmation_id": f"confirm_{abs(hash(action_id + summary))}",
            "action_id": action_id,
            "summary": summary,
            "risk_level": risk_level,
            "scopes": scopes,
            "status": "pending_user_confirmation",
            "confirmed": False,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
