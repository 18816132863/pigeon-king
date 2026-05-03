from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
from .schemas import ContinuousTask, TaskRunStatus, new_id, now_ts
from .storage import JsonStore


class ContinuousTaskRunner:
    """V95: long-running and recurring task registry.

    This module does not run background jobs by itself. It persists tasks and
    exposes deterministic next-step decisions so an external scheduler can call it.
    """

    def __init__(self, root: str | Path = ".autonomy_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "continuous_tasks.json")

    def create(self, title: str, goal: str, cadence: str, next_run_hint: str = "") -> ContinuousTask:
        task = ContinuousTask(
            id=new_id("ctask"),
            title=title,
            goal=goal,
            cadence=cadence,
            status=TaskRunStatus.CREATED,
            next_run_hint=next_run_hint,
        )
        self.store.append(self._to_dict(task))
        return task

    def mark_run(self, task_id: str, status: TaskRunStatus, metadata: Optional[Dict] = None) -> ContinuousTask:
        data = self.store.read([])
        for item in data:
            if item["id"] == task_id:
                item["status"] = status.value
                item["last_run_at"] = now_ts()
                item.setdefault("metadata", {}).update(metadata or {})
                self.store.write(data)
                return self._from_dict(item)
        raise KeyError(f"unknown task_id: {task_id}")

    def due(self) -> List[ContinuousTask]:
        # Deterministic MVP: CREATED/PARTIAL/FAILED tasks are due.
        due_status = {TaskRunStatus.CREATED.value, TaskRunStatus.PARTIAL.value, TaskRunStatus.FAILED.value}
        return [self._from_dict(x) for x in self.store.read([]) if x.get("status") in due_status]

    def list_tasks(self) -> List[ContinuousTask]:
        return [self._from_dict(x) for x in self.store.read([])]

    def _to_dict(self, t: ContinuousTask) -> Dict:
        return {
            "id": t.id,
            "title": t.title,
            "goal": t.goal,
            "cadence": t.cadence,
            "status": t.status.value,
            "last_run_at": t.last_run_at,
            "next_run_hint": t.next_run_hint,
            "metadata": t.metadata,
        }

    def _from_dict(self, item: Dict) -> ContinuousTask:
        return ContinuousTask(
            id=item["id"],
            title=item["title"],
            goal=item["goal"],
            cadence=item["cadence"],
            status=TaskRunStatus(item.get("status", TaskRunStatus.CREATED.value)),
            last_run_at=item.get("last_run_at"),
            next_run_hint=item.get("next_run_hint", ""),
            metadata=dict(item.get("metadata", {})),
        )
