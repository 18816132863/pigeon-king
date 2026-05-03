"""Append-only audit ledger for pending-access autonomous runs."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping


@dataclass
class AuditEvent:
    event_id: str
    event_type: str
    created_at: str
    payload: Dict[str, Any]
    real_side_effect: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PendingAuditLedger:
    """In-memory append-only audit ledger.

    The ledger is intentionally side-effect free in the pending-access state.
    It captures decisions, blocks, simulated execution, recovery and approval packets.
    """

    def __init__(self) -> None:
        self._events: List[AuditEvent] = []

    def append(self, event_type: str, payload: Mapping[str, Any] | None = None) -> Dict[str, Any]:
        event = AuditEvent(
            event_id=f"audit_{len(self._events) + 1:06d}",
            event_type=event_type,
            created_at=datetime.now(timezone.utc).isoformat(),
            payload=dict(payload or {}),
            real_side_effect=False,
        )
        self._events.append(event)
        return event.to_dict()

    def export(self) -> Dict[str, Any]:
        events = [event.to_dict() for event in self._events]
        return {
            "status": "audit_ledger_ready",
            "event_count": len(events),
            "real_side_effects": sum(1 for event in events if event.get("real_side_effect") is True),
            "events": events,
            "append_only": True,
            "replayable": True,
        }

    def has_event(self, event_type: str) -> bool:
        return any(event.event_type == event_type for event in self._events)
