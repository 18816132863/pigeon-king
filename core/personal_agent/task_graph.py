# -*- coding: utf-8 -*-
"""V86 task graph builder and safe dry-run executor."""
from __future__ import annotations

from hashlib import sha256
from typing import Dict, Iterable, List, Set

from .policy_judge import PolicyJudge
from .schemas import GoalSpec, NodeStatus, NodeType, RiskLevel, TaskGraph, TaskNode, utc_now


class TaskGraphBuilder:
    def __init__(self, judge: PolicyJudge | None = None):
        self.judge = judge or PolicyJudge()

    def build(self, goal: GoalSpec) -> TaskGraph:
        graph_id = "graph_" + sha256(goal.goal_id.encode("utf-8")).hexdigest()[:16]
        nodes: List[TaskNode] = [
            TaskNode("n1", "理解目标并标准化 GoalSpec", NodeType.REASONING, "understand_goal", risk_level=RiskLevel.L0),
            TaskNode("n2", "法典与风险裁判", NodeType.POLICY, "judge_goal_policy", depends_on=["n1"], risk_level=RiskLevel.L1),
            TaskNode("n3", "能力解析与缺口判断", NodeType.CAPABILITY_RESOLUTION, "resolve_capabilities", depends_on=["n2"], risk_level=RiskLevel.L1),
            TaskNode("n4", "模型与工具路由规划", NodeType.MODEL_ROUTING, "route_model_and_tools", depends_on=["n3"], risk_level=RiskLevel.L1),
        ]

        last_ids = ["n4"]
        for idx, objective in enumerate(goal.objectives or [], 1):
            risk = self._risk_for_objective(goal, objective)
            requires_approval = risk in (RiskLevel.L3, RiskLevel.L4)
            node = TaskNode(
                node_id=f"exec_{idx}",
                title=objective.get("title", f"执行子目标 {idx}"),
                node_type=NodeType.TOOL_EXECUTION if risk != RiskLevel.L0 else NodeType.REASONING,
                action="execute_objective",
                depends_on=list(last_ids),
                risk_level=risk,
                requires_approval=requires_approval,
                required_capabilities=list(objective.get("required_capabilities", [])),
            )
            nodes.append(node)
            last_ids = [node.node_id]

        if goal.approval_points:
            nodes.append(TaskNode(
                "approval_gate",
                "高风险动作审批中断点",
                NodeType.APPROVAL,
                "approval_interrupt",
                depends_on=list(last_ids),
                risk_level=RiskLevel.L4,
                requires_approval=True,
            ))
            last_ids = ["approval_gate"]

        nodes.extend([
            TaskNode("verify", "结果验收与闭环检查", NodeType.VERIFICATION, "verify_result", depends_on=list(last_ids), risk_level=RiskLevel.L1),
            TaskNode("learn", "经验回写与偏好更新", NodeType.MEMORY_WRITEBACK, "write_experience", depends_on=["verify"], risk_level=RiskLevel.L1),
        ])

        self._apply_policy(nodes, goal)
        return TaskGraph(
            graph_id=graph_id,
            goal=goal,
            nodes=nodes,
            completion_criteria=list(goal.success_criteria),
        )

    def _risk_for_objective(self, goal: GoalSpec, objective: Dict[str, object]) -> RiskLevel:
        hints = set(goal.risk_hints or [])
        title = str(objective.get("title", ""))
        if hints & {"money", "delete", "install_code", "privacy", "system_change"}:
            return RiskLevel.L4
        if hints & {"external_send"}:
            return RiskLevel.L3
        if any(w in title for w in ("覆盖", "修改", "写入", "更新")):
            return RiskLevel.L2
        return RiskLevel.L1

    def _apply_policy(self, nodes: List[TaskNode], goal: GoalSpec) -> None:
        goal_decision = self.judge.decide_goal_risk(goal.risk_hints)
        for node in nodes:
            if node.node_type in {NodeType.POLICY, NodeType.REASONING, NodeType.CAPABILITY_RESOLUTION, NodeType.MODEL_ROUTING, NodeType.VERIFICATION, NodeType.MEMORY_WRITEBACK}:
                decision = self.judge.decide({"action": node.action, "risk_hints": ["low"]})
            else:
                decision = self.judge.decide({"action": node.action, "risk_hints": goal.risk_hints, "external": node.requires_approval})
            if node.node_id == "approval_gate":
                decision = goal_decision
            node.policy_decision = decision.to_dict()
            node.requires_approval = node.requires_approval or decision.approval_required or decision.strong_approval_required
            node.risk_level = decision.risk_level if node.node_id == "approval_gate" else node.risk_level
            node.updated_at = utc_now()


class TaskGraphExecutor:
    """Safe executor: advances planning/low-risk nodes; blocks risky nodes.

    It does not perform real world side effects. Real tool invocation should be
    wired later through existing capability/route layers after approvals.
    """

    TERMINAL = {NodeStatus.COMPLETED, NodeStatus.FAILED, NodeStatus.BLOCKED_APPROVAL, NodeStatus.BLOCKED_POLICY, NodeStatus.SKIPPED}

    def run_safe(self, graph: TaskGraph, approvals: Iterable[str] | None = None, execute_low_risk: bool = True) -> TaskGraph:
        approvals_set = set(approvals or [])
        node_map = {n.node_id: n for n in graph.nodes}
        progressed = True
        while progressed:
            progressed = False
            for node in graph.nodes:
                if node.status != NodeStatus.PENDING:
                    continue
                if any(node_map[d].status != NodeStatus.COMPLETED for d in node.depends_on):
                    continue
                progressed = True
                self._advance_node(node, approvals_set, execute_low_risk)
        graph.updated_at = utc_now()
        return graph

    def _advance_node(self, node: TaskNode, approvals: Set[str], execute_low_risk: bool) -> None:
        decision = (node.policy_decision or {}).get("decision", "allow")
        if decision == "block":
            node.status = NodeStatus.BLOCKED_POLICY
            node.error = "blocked_by_policy"
        elif node.requires_approval and node.node_id not in approvals:
            node.status = NodeStatus.BLOCKED_APPROVAL
            node.output = {"reason": "approval_required", "risk_level": node.risk_level.value}
        elif node.risk_level in {RiskLevel.L0, RiskLevel.L1} and execute_low_risk:
            node.status = NodeStatus.COMPLETED
            node.output = {"ok": True, "mode": "safe_dry_run", "node_type": node.node_type.value}
        elif node.risk_level == RiskLevel.L2:
            node.status = NodeStatus.READY
            node.output = {"ok": True, "mode": "preview_ready", "requires_preview": True}
        else:
            node.status = NodeStatus.BLOCKED_APPROVAL
            node.output = {"reason": "risk_requires_approval", "risk_level": node.risk_level.value}
        node.updated_at = utc_now()

    def summary(self, graph: TaskGraph) -> Dict[str, object]:
        counts: Dict[str, int] = {}
        for node in graph.nodes:
            counts[node.status.value] = counts.get(node.status.value, 0) + 1
        return {
            "graph_id": graph.graph_id,
            "goal_id": graph.goal.goal_id,
            "statuses": counts,
            "terminal": all(n.status in self.TERMINAL or n.status == NodeStatus.READY for n in graph.nodes),
            "success": all(n.status == NodeStatus.COMPLETED for n in graph.nodes if not n.requires_approval),
            "blocked_for_approval": [n.node_id for n in graph.nodes if n.status == NodeStatus.BLOCKED_APPROVAL],
        }
