from __future__ import annotations

from typing import Any

from .mission_graph import MissionGraph
from .proactive_observer import ProactiveObserver
from .mission_priority_engine import MissionPriorityEngine


class MissionControlCenter:
    """Top-level mission control for one-sentence goals and proactive missions."""

    def __init__(self) -> None:
        self.observer = ProactiveObserver()
        self.priority = MissionPriorityEngine()

    def build_mission(self, goal: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        observed = self.observer.observe(context)
        graph = MissionGraph.from_goal(goal).to_dict()
        priority = self.priority.score(graph)
        requires_confirmation = priority["max_risk"] in {"L3", "L4", "BLOCKED"} or any("自动安装" in n["objective"] for n in graph["nodes"])
        return {
            "status": "mission_ready",
            "mission_shape": "Proactive Mission Control",
            "observed": observed,
            "mission": graph,
            "priority": priority,
            "requires_confirmation": requires_confirmation,
            "next_gate": "strong_confirmation" if requires_confirmation else "runtime_policy_gate",
        }
