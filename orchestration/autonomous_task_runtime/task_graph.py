"""Task graph compiler for long-horizon autonomous pending-access runs."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from governance.embodied_pending_state import classify_action_semantics


@dataclass
class TaskNode:
    node_id: str
    title: str
    action: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)
    checkpoint_required: bool = True
    semantic: Dict[str, Any] = field(default_factory=dict)
    expected_outcome: str = "prepared_or_sandboxed"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TaskGraph:
    graph_id: str
    goal: str
    constraints: Dict[str, Any]
    nodes: List[TaskNode]
    completion_definition: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["nodes"] = [node.to_dict() for node in self.nodes]
        return data


class AutonomousTaskGraphCompiler:
    """Compile a user goal into an auditable task graph.

    In V78 this is intentionally deterministic and conservative: every node receives
    an explicit semantic class, dependencies, a checkpoint and a non-live outcome.
    """

    def compile(self, goal: str, context: Mapping[str, Any] | None = None) -> TaskGraph:
        context = dict(context or {})
        requested_actions = list(context.get("actions") or [])
        if not requested_actions:
            requested_actions = [
                {"op_name": "read_context", "summary": "读取上下文与已有资料"},
                {"op_name": "analyze_goal", "summary": "分析目标与约束"},
                {"op_name": "prepare_execution_plan", "summary": "生成待执行计划"},
                {"op_name": "mock_external_send", "summary": "生成待发送草稿", "semantic_class": "external_send"},
                {"op_name": "mock_payment_checkout", "summary": "生成待付款审批包", "payment": True},
            ]
        nodes: List[TaskNode] = []
        previous_id = ""
        for idx, action in enumerate(requested_actions, start=1):
            semantic = classify_action_semantics(action).to_dict()
            node_id = f"node_{idx:03d}"
            deps = [previous_id] if previous_id else []
            if action.get("dependencies"):
                deps = list(action.get("dependencies") or [])
            if semantic["is_commit_action"]:
                expected = "approval_packet_or_mock_contract_only"
            elif semantic["semantic_class"] == "simulate":
                expected = "sandbox_replay"
            else:
                expected = "prepared_or_sandboxed"
            nodes.append(TaskNode(
                node_id=node_id,
                title=str(action.get("summary") or action.get("op_name") or f"task_{idx}"),
                action=dict(action),
                dependencies=deps,
                checkpoint_required=True,
                semantic=semantic,
                expected_outcome=expected,
            ))
            previous_id = node_id
        return TaskGraph(
            graph_id="task_graph_v78_001",
            goal=goal,
            constraints={
                "mode": "autonomous_pending_access",
                "real_world_connected": False,
                "real_side_effect_allowed": False,
                "commit_actions": "approval_packet_or_mock_only",
                "payment_signature_physical": "hard_cutoff",
                "external_send": "draft_or_pending_outbox_only",
                "resume_after_interrupt": "checkpoint_only",
            },
            nodes=nodes,
            completion_definition={
                "all_non_commit_nodes_sandboxed": True,
                "all_commit_nodes_blocked_or_approval_pack": True,
                "audit_replay_available": True,
                "no_real_side_effects": True,
            },
        )
