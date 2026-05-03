from __future__ import annotations
from typing import Any, Dict
from datetime import datetime, timezone

class ExecutionTraceRecorder:
    def __init__(self) -> None:
        self.records = []
    def record(self, action: dict | None, outcome: dict | None) -> Dict[str, Any]:
        record = {
            "trace_id": f"trace_{len(self.records)+1:06d}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "action": dict(action or {}),
            "outcome": dict(outcome or {}),
            "real_side_effect": False,
        }
        self.records.append(record)
        return record
