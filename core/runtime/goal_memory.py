from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class GoalRecord:
    goal: str
    status: str
    priority: int
    risk_level: str
    learned_preferences: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class GoalMemory:
    """In-memory goal ledger contract.

    Real persistence can later bind to sqlite/postgres/vector memory.
    This file defines the stable interface so the runtime can evolve safely.
    """

    def __init__(self) -> None:
        self.records: list[GoalRecord] = []

    def add(self, goal: str, status: str = "planned", priority: int = 50, risk_level: str = "L1") -> GoalRecord:
        record = GoalRecord(goal=goal, status=status, priority=priority, risk_level=risk_level)
        self.records.append(record)
        return record

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return [r.__dict__ for r in self.records[-limit:]]

    def learn_from_result(self, goal: str, result: dict[str, Any]) -> dict[str, Any]:
        signal = {
            "goal": goal,
            "success": bool(result.get("success", False)),
            "style": result.get("style", "unknown"),
            "risk_feedback": result.get("risk_feedback", "unchanged"),
        }
        if self.records:
            self.records[-1].learned_preferences.append(str(signal))
        return signal
