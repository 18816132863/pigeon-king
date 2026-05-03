from __future__ import annotations
from pathlib import Path
from .schemas import ControlArtifact, PlaneStatus, new_id
from .storage import JsonStore

class EventSourcingLedger:
    """V201: append-only event sourcing ledger."""
    def __init__(self, root: str | Path = ".production_control_plane_state"):
        self.store = JsonStore(Path(root) / "event_sourcing_ledger.json")
    def append(self, event_type: str, payload: dict) -> ControlArtifact:
        event = {"id": new_id("event"), "type": event_type, "payload": payload}
        self.store.append(event)
        return ControlArtifact(new_id("ledger"), "event_sourcing_ledger", "ledger", PlaneStatus.READY, 0.9, {"last_event": event, "total": len(self.store.read([]))})
