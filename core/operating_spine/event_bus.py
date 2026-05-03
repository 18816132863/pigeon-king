from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
from .schemas import SpineEvent, EventSeverity, new_id, to_dict
from .storage import JsonStore


class EventBus:
    """V117: unified event bus for all agent layers."""

    def __init__(self, root: str | Path = ".operating_spine_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "spine_events.json")

    def publish(self, run_id: str, topic: str, message: str, severity: EventSeverity = EventSeverity.INFO, payload: Optional[Dict] = None) -> SpineEvent:
        event = SpineEvent(
            id=new_id("event"),
            run_id=run_id,
            topic=topic,
            severity=severity,
            message=message,
            payload=payload or {},
        )
        self.store.append(to_dict(event))
        return event

    def list_run(self, run_id: str) -> List[SpineEvent]:
        return [self._from_dict(x) for x in self.store.read([]) if x.get("run_id") == run_id]

    def count(self, run_id: str | None = None) -> int:
        data = self.store.read([])
        if run_id is None:
            return len(data)
        return sum(1 for x in data if x.get("run_id") == run_id)

    def _from_dict(self, item: Dict) -> SpineEvent:
        return SpineEvent(
            id=item["id"],
            run_id=item["run_id"],
            topic=item["topic"],
            severity=EventSeverity(item["severity"]),
            message=item["message"],
            payload=dict(item.get("payload", {})),
            created_at=float(item.get("created_at", 0.0)),
        )
