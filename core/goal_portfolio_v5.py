"""V46.0 Goal Portfolio V5.

Turns isolated user goals into a governed portfolio with horizon, priority,
constraints, risk boundary and done definition. This is an orchestration-facing
core model, not a new architecture layer.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib
import json

VALID_HORIZONS = {"immediate", "today", "week", "month", "long_term"}

@dataclass
class GoalContractV5:
    goal_id: str
    objective: str
    horizon: str = "immediate"
    priority: int = 50
    constraints: Dict[str, Any] = field(default_factory=dict)
    risk_boundary: str = "normal"
    done_definition: List[str] = field(default_factory=list)
    approval_points: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @staticmethod
    def build(objective: str, horizon: str = "immediate", priority: int = 50,
              constraints: Optional[Dict[str, Any]] = None,
              risk_boundary: str = "normal",
              done_definition: Optional[List[str]] = None,
              approval_points: Optional[List[str]] = None) -> "GoalContractV5":
        if not objective or not objective.strip():
            raise ValueError("objective is required")
        if horizon not in VALID_HORIZONS:
            horizon = "immediate"
        priority = max(0, min(100, int(priority)))
        payload = json.dumps({"objective": objective.strip(), "horizon": horizon, "priority": priority}, ensure_ascii=False, sort_keys=True)
        goal_id = "goal_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
        return GoalContractV5(
            goal_id=goal_id,
            objective=objective.strip(),
            horizon=horizon,
            priority=priority,
            constraints=constraints or {},
            risk_boundary=risk_boundary,
            done_definition=done_definition or ["all required steps have verified receipts"],
            approval_points=approval_points or [],
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class GoalPortfolioV5:
    def __init__(self) -> None:
        self._goals: Dict[str, GoalContractV5] = {}

    def add(self, goal: GoalContractV5) -> GoalContractV5:
        self._goals[goal.goal_id] = goal
        return goal

    def list_ordered(self) -> List[GoalContractV5]:
        horizon_rank = {"immediate": 0, "today": 1, "week": 2, "month": 3, "long_term": 4}
        return sorted(self._goals.values(), key=lambda g: (horizon_rank.get(g.horizon, 9), -g.priority, g.created_at))

    def next_goal(self) -> Optional[GoalContractV5]:
        ordered = self.list_ordered()
        return ordered[0] if ordered else None

    def snapshot(self) -> Dict[str, Any]:
        return {"count": len(self._goals), "goals": [g.to_dict() for g in self.list_ordered()]}
