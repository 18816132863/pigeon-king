# -*- coding: utf-8 -*-
"""V86 personal execution agent data contracts.

The module is intentionally dependency-light and side-effect free.  It defines
one contract for goal compilation, policy judging, task graph execution,
verification and experience writeback.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Any, Dict, List, Optional
import json


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RiskLevel(str, Enum):
    L0 = "L0"  # pure reasoning / no side effect
    L1 = "L1"  # local reversible / low risk
    L2 = "L2"  # local mutation / preview required
    L3 = "L3"  # external effect / approval required
    L4 = "L4"  # high impact / strong approval required
    L5 = "L5"  # blocked by hard code


class Decision(str, Enum):
    ALLOW = "allow"
    PREVIEW_ONLY = "preview_only"
    REQUIRE_APPROVAL = "require_approval"
    REQUIRE_STRONG_APPROVAL = "require_strong_approval"
    REQUIRE_CLARIFICATION = "require_clarification"
    BLOCK = "block"


class NodeStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED_APPROVAL = "blocked_for_approval"
    BLOCKED_POLICY = "blocked_by_policy"
    SKIPPED = "skipped"


class NodeType(str, Enum):
    REASONING = "reasoning"
    POLICY = "policy"
    CAPABILITY_RESOLUTION = "capability_resolution"
    MODEL_ROUTING = "model_routing"
    TOOL_EXECUTION = "tool_execution"
    APPROVAL = "approval"
    VERIFICATION = "verification"
    MEMORY_WRITEBACK = "memory_writeback"
    CAPABILITY_GAP = "capability_gap"


@dataclass
class GoalSpec:
    goal_id: str
    raw_request: str
    objective: str
    objectives: List[Dict[str, Any]] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)
    information_sources: List[str] = field(default_factory=list)
    risk_hints: List[str] = field(default_factory=list)
    approval_points: List[str] = field(default_factory=list)
    time_scope: str = "unspecified"
    priority: str = "normal"
    autonomy_mode: str = "bounded_autonomy"
    created_at: str = field(default_factory=utc_now)

    @classmethod
    def new_id(cls, text: str) -> str:
        return "goal_" + sha256(text.strip().encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


@dataclass
class PolicyDecision:
    decision: Decision
    risk_level: RiskLevel
    reasons: List[str] = field(default_factory=list)
    approval_required: bool = False
    strong_approval_required: bool = False
    can_auto_execute: bool = False
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["decision"] = self.decision.value
        data["risk_level"] = self.risk_level.value
        return data


@dataclass
class TaskNode:
    node_id: str
    title: str
    node_type: NodeType
    action: str
    depends_on: List[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.L1
    status: NodeStatus = NodeStatus.PENDING
    requires_approval: bool = False
    required_capabilities: List[str] = field(default_factory=list)
    route_hint: Optional[str] = None
    model_hint: Optional[str] = None
    tool_hint: Optional[str] = None
    policy_decision: Optional[Dict[str, Any]] = None
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["node_type"] = self.node_type.value
        data["risk_level"] = self.risk_level.value
        data["status"] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskNode":
        d = dict(data)
        d["node_type"] = NodeType(d.get("node_type", NodeType.REASONING.value))
        d["risk_level"] = RiskLevel(d.get("risk_level", RiskLevel.L1.value))
        d["status"] = NodeStatus(d.get("status", NodeStatus.PENDING.value))
        return cls(**d)


@dataclass
class TaskGraph:
    graph_id: str
    goal: GoalSpec
    nodes: List[TaskNode] = field(default_factory=list)
    completion_criteria: List[str] = field(default_factory=list)
    durable: bool = True
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "goal": self.goal.to_dict(),
            "nodes": [n.to_dict() for n in self.nodes],
            "completion_criteria": list(self.completion_criteria),
            "durable": self.durable,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskGraph":
        goal = GoalSpec(**data["goal"])
        nodes = [TaskNode.from_dict(n) for n in data.get("nodes", [])]
        return cls(
            graph_id=data["graph_id"],
            goal=goal,
            nodes=nodes,
            completion_criteria=data.get("completion_criteria", []),
            durable=data.get("durable", True),
            created_at=data.get("created_at", utc_now()),
            updated_at=data.get("updated_at", utc_now()),
        )


@dataclass
class ExecutionPlan:
    graph_id: str
    node_plans: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    can_auto_run_nodes: List[str] = field(default_factory=list)
    approval_nodes: List[str] = field(default_factory=list)
    blocked_nodes: List[str] = field(default_factory=list)
    capability_gaps: List[Dict[str, Any]] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VerificationResult:
    graph_id: str
    passed: bool
    score: float
    completed_nodes: int
    blocked_nodes: int
    failed_nodes: int
    reasons: List[str] = field(default_factory=list)
    next_actions: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExperienceRecord:
    graph_id: str
    goal_id: str
    objective: str
    success: bool
    verification_score: float
    blocked_reasons: List[str] = field(default_factory=list)
    reusable_procedure: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
