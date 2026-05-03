from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
from .schemas import TraceEvent, new_id
from .storage import JsonStore


class TraceAudit:
    """V92: trace and audit log for autonomy runs."""

    def __init__(self, root: str | Path = ".autonomy_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "trace_events.json")

    def record(self, run_id: str, event_type: str, message: str, payload: Optional[Dict] = None) -> TraceEvent:
        event = TraceEvent(
            id=new_id("trace"),
            run_id=run_id,
            event_type=event_type,
            message=message,
            payload=payload or {},
        )
        self.store.append(self._to_dict(event))
        return event

    def list_run(self, run_id: str) -> List[TraceEvent]:
        return [self._from_dict(x) for x in self.store.read([]) if x.get("run_id") == run_id]

    def summarize(self, run_id: str) -> Dict:
        events = self.list_run(run_id)
        counts = {}
        for e in events:
            counts[e.event_type] = counts.get(e.event_type, 0) + 1
        return {"run_id": run_id, "events": len(events), "by_type": counts}

    def _to_dict(self, e: TraceEvent) -> Dict:
        return {
            "id": e.id,
            "run_id": e.run_id,
            "event_type": e.event_type,
            "message": e.message,
            "payload": e.payload,
            "created_at": e.created_at,
        }

    def _from_dict(self, item: Dict) -> TraceEvent:
        return TraceEvent(
            id=item["id"],
            run_id=item["run_id"],
            event_type=item["event_type"],
            message=item["message"],
            payload=dict(item.get("payload", {})),
            created_at=float(item.get("created_at", 0.0)),
        )
