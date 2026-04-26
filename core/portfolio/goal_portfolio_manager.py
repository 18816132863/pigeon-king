from __future__ import annotations

from .task_backlog import TaskBacklog
from .progress_evaluator import ProgressEvaluator


class GoalPortfolioManager:
    """Manage multiple long-running goals instead of treating every prompt as isolated."""

    def __init__(self) -> None:
        self.goals: list[dict] = []
        self.backlog = TaskBacklog()
        self.evaluator = ProgressEvaluator()

    def add_goal(self, goal: str, horizon: str = "short", risk_level: str = "L1") -> dict:
        item = {
            "goal_id": f"goal_{len(self.goals)+1}",
            "goal": goal,
            "horizon": horizon,
            "risk_level": risk_level,
            "status": "planned",
        }
        self.goals.append(item)
        self.backlog.add(goal, priority=50, risk_level=risk_level)
        return item

    def snapshot(self) -> dict:
        portfolio = {"goals": self.goals, "tasks": self.backlog.list()}
        return {**portfolio, "progress": self.evaluator.evaluate(portfolio)}
