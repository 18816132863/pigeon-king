"""V47.0 Durable Run Ledger V5.

Append-only run ledger for mission lifecycle: goal -> task graph -> device serial lane
-> verification -> memory writeback. Designed for resumability and auditability.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import uuid

@dataclass
class RunEventV5:
    run_id: str
    event_type: str
    payload: Dict[str, Any]
    created_at: str

class DurableRunLedgerV5:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text(json.dumps({"version": "v47.0", "events": []}, ensure_ascii=False, indent=2), encoding="utf-8")

    def new_run_id(self) -> str:
        return "run_" + uuid.uuid4().hex[:16]

    def append(self, run_id: str, event_type: str, payload: Optional[Dict[str, Any]] = None) -> RunEventV5:
        event = RunEventV5(run_id=run_id, event_type=event_type, payload=payload or {}, created_at=datetime.now(timezone.utc).isoformat())
        data = json.loads(self.path.read_text(encoding="utf-8"))
        data.setdefault("events", []).append(asdict(event))
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return event

    def events_for(self, run_id: str) -> List[Dict[str, Any]]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return [e for e in data.get("events", []) if e.get("run_id") == run_id]

    def latest_state(self, run_id: str) -> Dict[str, Any]:
        events = self.events_for(run_id)
        state: Dict[str, Any] = {"run_id": run_id, "status": "unknown", "completed_steps": [], "pending_steps": []}
        for event in events:
            payload = event.get("payload", {})
            if event.get("event_type") == "status":
                state["status"] = payload.get("status", state["status"])
            elif event.get("event_type") == "step_completed":
                step = payload.get("step")
                if step and step not in state["completed_steps"]:
                    state["completed_steps"].append(step)
            elif event.get("event_type") == "pending_steps":
                state["pending_steps"] = payload.get("pending_steps", [])
        return state
