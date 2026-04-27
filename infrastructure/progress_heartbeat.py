"""
V24.2 Progress Heartbeat.

Layer: L6 Infrastructure.

Writes small state files for long-running tasks.  This complements
context_resume and prevents reliance on chat history after compaction.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json
import time


ARCHITECTURE_LAYER = "L6 Infrastructure"


@dataclass
class ProgressState:
    task_id: str
    current_phase: str
    completed_steps: list[str]
    pending_steps: list[str]
    next_command: str
    updated_at: float
    heartbeat_at: float
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProgressHeartbeat:
    def __init__(self, state_path: str | Path):
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        *,
        task_id: str,
        current_phase: str,
        completed_steps: list[str],
        pending_steps: list[str],
        next_command: str,
        metadata: dict[str, Any] | None = None,
    ) -> ProgressState:
        now = time.time()
        state = ProgressState(
            task_id=task_id,
            current_phase=current_phase,
            completed_steps=completed_steps,
            pending_steps=pending_steps,
            next_command=next_command,
            updated_at=now,
            heartbeat_at=now,
            metadata=metadata or {},
        )
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.state_path)
        return state

    def read(self) -> ProgressState | None:
        if not self.state_path.exists():
            return None
        data = json.loads(self.state_path.read_text(encoding="utf-8"))
        return ProgressState(**data)

    def is_stale(self, max_age_seconds: int = 180) -> bool:
        state = self.read()
        if not state:
            return False
        return (time.time() - state.heartbeat_at) > max_age_seconds
