"""V27.0 Durable Workflow Engine V3.

L3 Orchestration:
- Builds a durable task graph from an OperatingContract.
- Enforces that device-side actions are represented as serial nodes.
- Does not directly call device tools; L4 execution/outbox must do that.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Set
import json
import uuid


class NodeStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    PENDING_VERIFY = "pending_verify"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TaskNode:
    node_id: str
    name: str
    action_kind: str
    layer_owner: str
    depends_on: List[str] = field(default_factory=list)
    device_side_effect: bool = False
    reversible: bool = True
    timeout_profile: str = "default"
    verification_policy: str = "basic"
    status: NodeStatus = NodeStatus.QUEUED
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


@dataclass
class DurableTaskGraph:
    graph_id: str
    contract_id: str
    nodes: List[TaskNode]
    cursor: Optional[str] = None
    version: str = "v3"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "contract_id": self.contract_id,
            "cursor": self.cursor,
            "version": self.version,
            "nodes": [n.to_dict() for n in self.nodes],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DurableTaskGraph":
        nodes = []
        for raw in data["nodes"]:
            raw = dict(raw)
            raw["status"] = NodeStatus(raw["status"])
            nodes.append(TaskNode(**raw))
        return cls(graph_id=data["graph_id"], contract_id=data["contract_id"], nodes=nodes, cursor=data.get("cursor"), version=data.get("version", "v3"))

    def ready_nodes(self) -> List[TaskNode]:
        done = {n.node_id for n in self.nodes if n.status in (NodeStatus.COMPLETED, NodeStatus.SKIPPED)}
        ready = []
        for node in self.nodes:
            if node.status != NodeStatus.QUEUED:
                continue
            if all(dep in done for dep in node.depends_on):
                ready.append(node)
        return ready

    def has_blocking_pending_verify(self) -> bool:
        return any(n.status == NodeStatus.PENDING_VERIFY and n.device_side_effect for n in self.nodes)

    def assert_device_actions_serialized(self) -> bool:
        """Device nodes must form a chain, not parallel fan-out."""
        device_nodes = [n for n in self.nodes if n.device_side_effect]
        if len(device_nodes) <= 1:
            return True
        previous = device_nodes[0].node_id
        for node in device_nodes[1:]:
            if previous not in node.depends_on:
                return False
            previous = node.node_id
        return True


class DurableWorkflowCompilerV3:
    def build_from_contract(self, contract: Any) -> DurableTaskGraph:
        nodes: List[TaskNode] = []
        graph_id = "graph_" + uuid.uuid4().hex[:12]

        nodes.append(TaskNode(
            node_id="n1_goal_review",
            name="review_goal_contract",
            action_kind="internal_review",
            layer_owner="L3",
            verification_policy="contract_schema",
        ))

        last_device_node: Optional[str] = None
        raw_goal = getattr(contract, "raw_goal", "")
        device_terms = ["闹钟", "提醒", "日程", "通知", "打开", "设置", "文件", "GUI", "端侧"]
        device_actions = []
        if any(term in raw_goal for term in device_terms):
            # Large workflow default: break into common serial device-safe phases.
            device_actions = [
                ("n2_device_capability_probe", "probe_device_capability", "device_probe", "device_probe"),
                ("n3_device_prepare", "prepare_device_action", "device_prepare", "device_prepare"),
                ("n4_device_execute", "execute_device_action", "device_action", "device_receipt_or_pending_verify"),
                ("n5_device_verify", "verify_device_result", "device_verify", "two_phase_verify"),
            ]

        prev = "n1_goal_review"
        for node_id, name, action_kind, verify in device_actions:
            deps = [prev]
            if last_device_node and last_device_node not in deps:
                deps.append(last_device_node)
            node = TaskNode(
                node_id=node_id,
                name=name,
                action_kind=action_kind,
                layer_owner="L4",
                depends_on=deps,
                device_side_effect=True,
                reversible=False if "execute" in name else True,
                timeout_profile="device_safe",
                verification_policy=verify,
            )
            nodes.append(node)
            prev = node_id
            last_device_node = node_id

        nodes.append(TaskNode(
            node_id="n6_judge_gate",
            name="unified_judge_gate",
            action_kind="governance_check",
            layer_owner="L5",
            depends_on=[prev],
            verification_policy="judge_decision",
        ))
        nodes.append(TaskNode(
            node_id="n7_memory_writeback",
            name="guarded_memory_writeback",
            action_kind="memory_write",
            layer_owner="L2",
            depends_on=["n6_judge_gate"],
            verification_policy="memory_guard",
        ))
        nodes.append(TaskNode(
            node_id="n8_completion_report",
            name="completion_report",
            action_kind="report",
            layer_owner="L3",
            depends_on=["n7_memory_writeback"],
            verification_policy="done_definition",
        ))

        graph = DurableTaskGraph(graph_id=graph_id, contract_id=getattr(contract, "contract_id", "unknown"), nodes=nodes)
        if not graph.assert_device_actions_serialized():
            raise ValueError("device actions are not serialized")
        return graph
