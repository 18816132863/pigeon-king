"""
V25.3 Durable Task Graph V2

A minimal durable graph model with serial / parallel eligibility, wait points and
approval interrupts. It is schema-based and can be persisted by context_resume.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, Iterable, List, Optional


@dataclass
class TaskNodeV2:
    node_id: str
    action: str
    layer: str
    end_side: bool = False
    depends_on: List[str] = field(default_factory=list)
    approval_required: bool = False
    verification_required: bool = True
    status: str = "queued"

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


@dataclass
class TaskGraphV2:
    goal_id: str
    nodes: List[TaskNodeV2]

    def ready_nodes(self) -> List[TaskNodeV2]:
        completed = {node.node_id for node in self.nodes if node.status == "completed"}
        return [
            node for node in self.nodes
            if node.status == "queued" and all(dep in completed for dep in node.depends_on)
        ]

    def end_side_nodes(self) -> List[TaskNodeV2]:
        return [node for node in self.nodes if node.end_side]

    def to_dict(self) -> Dict[str, object]:
        return {"goal_id": self.goal_id, "nodes": [node.to_dict() for node in self.nodes]}


class TaskGraphBuilderV2:
    def from_goal(self, goal_id: str, actions: Iterable[Dict[str, object]]) -> TaskGraphV2:
        nodes: List[TaskNodeV2] = []
        previous_end_side: Optional[str] = None
        for idx, action in enumerate(actions):
            end_side = bool(action.get("end_side", False))
            deps = list(action.get("depends_on", []))
            # Enforce global end-side serial dependency within the graph.
            if end_side and previous_end_side and previous_end_side not in deps:
                deps.append(previous_end_side)
            node = TaskNodeV2(
                node_id=str(action.get("node_id") or f"node_{idx+1}"),
                action=str(action.get("action")),
                layer=str(action.get("layer", "L4 Execution")),
                end_side=end_side,
                depends_on=deps,
                approval_required=bool(action.get("approval_required", False)),
                verification_required=bool(action.get("verification_required", True)),
            )
            if end_side:
                previous_end_side = node.node_id
            nodes.append(node)
        return TaskGraphV2(goal_id=goal_id, nodes=nodes)
