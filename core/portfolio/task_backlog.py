from __future__ import annotations


class TaskBacklog:
    def __init__(self) -> None:
        self.tasks: list[dict] = []

    def add(self, title: str, priority: int = 50, risk_level: str = "L1") -> dict:
        task = {
            "task_id": f"task_{len(self.tasks)+1}",
            "title": title,
            "priority": priority,
            "risk_level": risk_level,
            "status": "planned",
        }
        self.tasks.append(task)
        return task

    def list(self) -> list[dict]:
        return sorted(self.tasks, key=lambda x: (x["priority"], x["risk_level"]))
