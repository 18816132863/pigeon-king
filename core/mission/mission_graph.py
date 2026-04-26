from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MissionNode:
    node_id: str
    objective: str
    node_type: str = "task"
    risk_level: str = "L1"
    status: str = "planned"
    depends_on: list[str] = field(default_factory=list)
    required_capabilities: list[str] = field(default_factory=list)
    verification: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__


@dataclass
class MissionGraph:
    mission_id: str
    objective: str
    nodes: list[MissionNode]
    status: str = "planned"

    def to_dict(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "objective": self.objective,
            "status": self.status,
            "nodes": [n.to_dict() for n in self.nodes],
        }

    @classmethod
    def from_goal(cls, goal: str) -> "MissionGraph":
        nodes = [
            MissionNode("observe", "理解目标和上下文", "observe", "L0", required_capabilities=["goal_modeling"], verification=["context_read"]),
            MissionNode("decide", "判断策略、风险和优先级", "decision", "L1", depends_on=["observe"], required_capabilities=["risk_judgement"], verification=["policy_check"]),
            MissionNode("plan", "生成任务链和验证链", "planning", "L1", depends_on=["decide"], required_capabilities=["task_graph"], verification=["graph_valid"]),
        ]
        if any(k in goal for k in ["没技能", "没方案", "找方案", "自动安装", "接入"]):
            nodes.append(MissionNode("acquire", "搜索方案并生成能力接入计划", "capability_acquisition", "L2", depends_on=["plan"], required_capabilities=["solution_search"], verification=["sandbox_plan", "rollback_plan"]))
        nodes.append(MissionNode("execute_gate", "执行前门控", "gate", "L2", depends_on=[nodes[-1].node_id], required_capabilities=["policy_gate"], verification=["strong_confirm_if_needed"]))
        nodes.append(MissionNode("learn", "结果验证和学习写回", "learning", "L1", depends_on=["execute_gate"], required_capabilities=["personal_learning"], verification=["writeback_audit"]))
        return cls(mission_id=f"mission_{abs(hash(goal))}", objective=goal, nodes=nodes)
