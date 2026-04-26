from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class StrategyRecord:
    goal: str
    selected_strategy: str
    risk_level: str
    outcome: str = "planned"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class StrategyMemory:
    """Stable contract for remembering which strategies work for the user."""

    def __init__(self) -> None:
        self.records: list[StrategyRecord] = []

    def add(self, goal: str, strategy: str, risk_level: str) -> StrategyRecord:
        record = StrategyRecord(goal=goal, selected_strategy=strategy, risk_level=risk_level)
        self.records.append(record)
        return record

    def recommend(self, goal: str) -> dict:
        if "压缩包" in goal or "一次性" in goal:
            return {"strategy": "deliver_artifact_first", "reason": "user_prefers_direct_artifact_delivery"}
        if "不要猜" in goal:
            return {"strategy": "strict_instruction_following", "reason": "user_dislikes_ambiguous_execution"}
        return {"strategy": "bounded_autonomous_plan", "reason": "default_safe_autonomy"}
