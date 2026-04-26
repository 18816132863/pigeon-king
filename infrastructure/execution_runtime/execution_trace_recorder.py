from __future__ import annotations

from datetime import datetime


class ExecutionTraceRecorder:
    def record(self, action: dict, outcome: dict) -> dict:
        return {
            "status": "trace_recorded",
            "action": action,
            "outcome": outcome,
            "created_at": datetime.utcnow().isoformat() + "Z",
        }
