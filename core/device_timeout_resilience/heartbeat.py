from __future__ import annotations

from pathlib import Path
from .schemas import Heartbeat, TimeoutStatus, new_id, to_dict
from .storage import JsonStore


class HeartbeatStore:
    """Heartbeat store so the operator can know a long task is alive."""

    def __init__(self, root: str | Path = ".timeout_resilience_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "heartbeats.json")

    def beat(self, job_id: str, step_id: str, status: TimeoutStatus, checkpoint_id: str, message: str) -> Heartbeat:
        hb = Heartbeat(
            id=new_id("heartbeat"),
            job_id=job_id,
            step_id=step_id,
            status=status,
            checkpoint_id=checkpoint_id,
            message=message,
        )
        self.store.append(to_dict(hb))
        return hb
