from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(order=True)
class ScheduledTask:
    priority: int
    task_id: str
    title: str
    risk_level: str = "L1"
    requires_confirmation: bool = False
    metadata: dict[str, Any] | None = None


class PriorityScheduler:
    """Schedule tasks by urgency, risk and user style."""

    def schedule(self, tasks: list[dict[str, Any]]) -> list[ScheduledTask]:
        scheduled: list[ScheduledTask] = []
        for index, task in enumerate(tasks):
            risk = task.get("risk_level", "L1")
            base = int(task.get("priority", 50))
            risk_penalty = {"L0": 0, "L1": 5, "L2": 15, "L3": 30, "L4": 50, "BLOCKED": 100}.get(risk, 20)
            scheduled.append(ScheduledTask(
                priority=base + risk_penalty,
                task_id=task.get("task_id", f"task_{index}"),
                title=task.get("title", task.get("step", "unnamed_task")),
                risk_level=risk,
                requires_confirmation=risk in {"L3", "L4", "BLOCKED"},
                metadata=task,
            ))
        return sorted(scheduled)
