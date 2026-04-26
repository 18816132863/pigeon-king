"""V10 task graph compiler for one-sentence goals."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TaskNode:
    id: str
    name: str
    node_type: str
    risk_level: str = "L1"
    requires_approval: bool = False
    depends_on: list[str] = field(default_factory=list)


@dataclass
class ExecutionGraph:
    graph_id: str
    nodes: list[TaskNode]
    completion_criteria: list[str]
    reversible: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "nodes": [n.__dict__ for n in self.nodes],
            "completion_criteria": list(self.completion_criteria),
            "reversible": self.reversible,
        }


class TaskGraphCompiler:
    def compile_from_goal_model(self, goal_model: dict[str, Any]) -> ExecutionGraph:
        raw = goal_model.get("objective") or goal_model.get("raw_goal") or "unknown_goal"
        required = goal_model.get("required_capabilities", [])
        risk_hints = goal_model.get("risk_hints", [])
        nodes = [
            TaskNode("n1", "understand_goal", "reasoning", "L0"),
            TaskNode("n2", "check_rules_and_risk", "governance", "L1", depends_on=["n1"]),
            TaskNode("n3", "resolve_capabilities", "capability_resolution", "L1", depends_on=["n2"]),
        ]
        if "solution_search" in required:
            nodes.append(TaskNode("n4", "search_solution", "research", "L1", depends_on=["n3"]))
        if "capability_extension" in required:
            nodes.append(TaskNode("n5", "sandbox_capability_extension", "self_extension", "L3", True, ["n3"]))
        nodes.append(TaskNode("n9", "verify_and_learn", "verification", "L1", depends_on=[nodes[-1].id]))
        return ExecutionGraph(
            graph_id="graph_" + str(abs(hash(raw)))[:10],
            nodes=nodes,
            completion_criteria=["safe_steps_finished", "result_verified", "learning_written_back"],
            reversible=not bool(risk_hints),
        )
