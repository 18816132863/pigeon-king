from __future__ import annotations

from pathlib import Path
from .schemas import JobRecord, JobStatus, RuntimeCommand, new_id, now_ts, to_dict
from .storage import JsonStore


class JobQueue:
    """V139: deterministic lightweight job queue."""

    def __init__(self, root: str | Path = ".runtime_activation_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "jobs.json")

    def enqueue(self, command: RuntimeCommand, title: str | None = None) -> JobRecord:
        job = JobRecord(
            id=new_id("job"),
            command_id=command.id,
            title=title or command.raw_text[:80],
            status=JobStatus.QUEUED,
        )
        self.store.append(to_dict(job))
        return job

    def run_next(self) -> JobRecord | None:
        data = self.store.read([])
        for item in data:
            if item.get("status") == JobStatus.QUEUED.value:
                item["status"] = JobStatus.RUNNING.value
                item["attempts"] = int(item.get("attempts", 0)) + 1
                item["updated_at"] = now_ts()
                if any(x in item.get("title", "") for x in ["发送", "转账", "删除", "安装"]):
                    item["status"] = JobStatus.WAITING_APPROVAL.value
                    item["result_summary"] = "approval required"
                else:
                    item["status"] = JobStatus.COMPLETED.value
                    item["result_summary"] = "dry-run completed"
                self.store.write(data)
                return self._from_dict(item)
        return None

    def list_jobs(self) -> list[JobRecord]:
        return [self._from_dict(x) for x in self.store.read([])]

    def _from_dict(self, item: dict) -> JobRecord:
        return JobRecord(
            id=item["id"],
            command_id=item["command_id"],
            title=item["title"],
            status=JobStatus(item["status"]),
            attempts=int(item.get("attempts", 0)),
            max_attempts=int(item.get("max_attempts", 2)),
            result_summary=item.get("result_summary", ""),
            created_at=float(item.get("created_at", 0.0)),
            updated_at=float(item.get("updated_at", 0.0)),
        )
