"""V66.0 Multi-Horizon Autonomy Planner.

Plans goals across immediate, daily, weekly and strategic horizons without
violating six-layer architecture boundaries. This module only creates
mission-level plans; execution remains in L4 and governance remains in L5.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any

VALID_HORIZONS = ("now", "today", "week", "long_term")

@dataclass
class HorizonGoal:
    goal_id: str
    title: str
    horizon: str = "now"
    priority: int = 5
    constraints: Dict[str, Any] = field(default_factory=dict)
    done_definition: str = "observable result verified"

@dataclass
class HorizonPlan:
    goals: List[HorizonGoal]
    execution_order: List[str]
    blocked: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

class MultiHorizonPlanner:
    layer = "L3_ORCHESTRATION"

    def normalize(self, goals: List[HorizonGoal]) -> List[HorizonGoal]:
        normalized = []
        for g in goals:
            horizon = g.horizon if g.horizon in VALID_HORIZONS else "now"
            normalized.append(HorizonGoal(
                goal_id=g.goal_id,
                title=g.title,
                horizon=horizon,
                priority=max(1, min(10, int(g.priority))),
                constraints=dict(g.constraints),
                done_definition=g.done_definition or "observable result verified",
            ))
        return normalized

    def plan(self, goals: List[HorizonGoal]) -> HorizonPlan:
        normalized = self.normalize(goals)
        order = sorted(normalized, key=lambda g: (VALID_HORIZONS.index(g.horizon), -g.priority, g.goal_id))
        blocked = [g.goal_id for g in order if g.constraints.get("requires_approval")]
        return HorizonPlan(
            goals=order,
            execution_order=[g.goal_id for g in order],
            blocked=blocked,
            notes=["planner only schedules; L5 decides approval; L4 executes"],
        )

def demo_plan() -> HorizonPlan:
    return MultiHorizonPlanner().plan([
        HorizonGoal("g1", "set meal reminder", "now", 8),
        HorizonGoal("g2", "review weekly missions", "week", 6, {"requires_approval": False}),
    ])
