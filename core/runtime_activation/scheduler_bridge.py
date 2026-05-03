from __future__ import annotations

from pathlib import Path
from .schemas import ScheduleRecord, ScheduleStatus, JobRecord, new_id, to_dict
from .storage import JsonStore


class SchedulerBridge:
    """V140: scheduler bridge without background execution."""

    def __init__(self, root: str | Path = ".runtime_activation_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "schedules.json")

    def create_once(self, title: str, linked_job: JobRecord, next_run_hint: str = "now") -> ScheduleRecord:
        rec = ScheduleRecord(
            id=new_id("schedule"),
            title=title,
            cadence="once",
            status=ScheduleStatus.DUE if next_run_hint == "now" else ScheduleStatus.CREATED,
            next_run_hint=next_run_hint,
            linked_job_id=linked_job.id,
        )
        self.store.append(to_dict(rec))
        return rec

    def due(self) -> list[ScheduleRecord]:
        return [self._from_dict(x) for x in self.store.read([]) if x.get("status") == ScheduleStatus.DUE.value]

    def _from_dict(self, item: dict) -> ScheduleRecord:
        return ScheduleRecord(
            id=item["id"],
            title=item["title"],
            cadence=item["cadence"],
            status=ScheduleStatus(item["status"]),
            next_run_hint=item["next_run_hint"],
            linked_job_id=item.get("linked_job_id"),
        )
