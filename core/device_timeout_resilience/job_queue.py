from __future__ import annotations

from pathlib import Path
from .schemas import DeviceJob, JobMode, TimeoutStatus, new_id, to_dict
from .storage import JsonStore


class ResumableJobQueue:
    """Durable queue for long device/connector jobs."""

    def __init__(self, root: str | Path = ".timeout_resilience_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "device_jobs.json")

    def enqueue(self, message: str, estimated_seconds: int, approval_required: bool, steps, checkpoint_id: str) -> DeviceJob:
        if approval_required:
            mode = JobMode.APPROVAL_WAIT
            status = TimeoutStatus.WAITING_APPROVAL
        elif estimated_seconds >= 45:
            mode = JobMode.FAST_ACK
            status = TimeoutStatus.RESUMABLE
        else:
            mode = JobMode.CHUNKED
            status = TimeoutStatus.QUEUED

        job = DeviceJob(
            id=new_id("devjob"),
            message=message,
            mode=mode,
            status=status,
            estimated_seconds=estimated_seconds,
            checkpoint_id=checkpoint_id,
            approval_required=approval_required,
            steps=steps,
        )
        self.store.append(to_dict(job))
        return job
