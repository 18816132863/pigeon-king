from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional
import time
import uuid

def now_ts() -> float:
    return time.time()

def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

class RiskLevel(str, Enum):
    L0_READONLY = "L0_readonly"
    L1_LOW = "L1_low"
    L2_REVERSIBLE = "L2_reversible"
    L3_EXTERNAL_SIDE_EFFECT = "L3_external_side_effect"
    L4_SENSITIVE_OR_IRREVERSIBLE = "L4_sensitive_or_irreversible"

class JudgeDecision(str, Enum):
    ALLOW = "allow"
    APPROVAL_REQUIRED = "approval_required"
    BLOCK = "block"

class TaskStatus(str, Enum):
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    SKIPPED = "skipped"

class MemoryKind(str, Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"

@dataclass
class GoalNode:
    id: str
    title: str
    priority: int
    completion_definition: str
    constraints: List[str] = field(default_factory=list)

@dataclass
class GoalContract:
    id: str
    raw_input: str
    objective: str
    goal_tree: List[GoalNode]
    constraints: List[str]
    non_goals: List[str]
    risk_level: RiskLevel
    automation_boundary: str
    approval_required: bool
    blocked: bool
    completion_definition: str
    information_sources: List[str]
    created_at: float = field(default_factory=now_ts)

@dataclass
class TaskNode:
    id: str
    title: str
    kind: str
    depends_on: List[str]
    status: TaskStatus
    risk_level: RiskLevel
    can_auto_execute: bool
    requires_approval: bool
    checkpoint_required: bool
    output: Dict[str, Any] = field(default_factory=dict)

@dataclass
class TaskGraph:
    id: str
    goal_contract_id: str
    nodes: List[TaskNode]
    edges: List[Dict[str, str]]
    checkpoint_id: str
    created_at: float = field(default_factory=now_ts)

@dataclass
class WorldCapability:
    name: str
    layer: str
    available: bool
    safe_default: bool
    description: str

@dataclass
class CapabilityGap:
    capability: str
    needed: bool
    available: bool
    safe_expansion_plan: List[str]
    approval_required: bool

@dataclass
class ExecutionTrace:
    id: str
    task_id: str
    status: TaskStatus
    decision: JudgeDecision
    summary: str
    evidence: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MemoryRecord:
    id: str
    kind: MemoryKind
    key: str
    value: Any
    confidence: float
    source: str
    created_at: float = field(default_factory=now_ts)

@dataclass
class AIShapeResult:
    run_id: str
    raw_input: str
    final_status: str
    judge_decision: JudgeDecision
    risk_level: RiskLevel
    goal_contract: GoalContract
    task_graph: TaskGraph
    information_sources: List[str]
    auto_executed_tasks: List[str]
    approval_tasks: List[str]
    blocked_tasks: List[str]
    checkpoint_id: str
    execution_traces: List[ExecutionTrace]
    capability_gaps: List[CapabilityGap]
    recovery_plan: List[str]
    memory_writes: List[MemoryRecord]
    world_capabilities: List[WorldCapability]
    completion_report: Dict[str, Any]

def to_dict(obj: Any) -> Dict[str, Any]:
    data = asdict(obj)
    for k, v in list(data.items()):
        if isinstance(v, Enum):
            data[k] = v.value
        elif isinstance(v, list):
            new_list = []
            for x in v:
                if isinstance(x, Enum):
                    new_list.append(x.value)
                elif hasattr(x, "__dataclass_fields__"):
                    new_list.append(to_dict(x))
                else:
                    new_list.append(x)
            data[k] = new_list
        elif isinstance(v, dict):
            data[k] = {kk: (vv.value if isinstance(vv, Enum) else vv) for kk, vv in v.items()}
        elif hasattr(v, "__dataclass_fields__"):
            data[k] = to_dict(v)
    return data
