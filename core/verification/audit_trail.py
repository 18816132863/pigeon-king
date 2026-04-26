from __future__ import annotations

from datetime import datetime


class AuditTrail:
    def build_event(self, event_type: str, payload: dict) -> dict:
        return {
            "event_type": event_type,
            "payload": payload,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "audit_required": True,
        }
