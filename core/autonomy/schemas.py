from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import time
import uuid


class RiskLevel(str, Enum):
    L0 = "L0_readonly"
    L1 = "L1_low_risk"
    L2 = "L2_reversible"
    L3 = "L3_external_side_effect"
    L4 = "L4_sensitive_or_irreversible"


class MemoryKind(str, Enum):
    PROFILE = "profile"
    PREFERENCE = "preference"
    EPISODIC = "episodic"
    PROCEDURAL = "procedural"
    RELATIONSHIP = "relationship"
    PROJECT = "project"


class ConnectorKind(str, Enum):
    LOCAL = "local"
    MCP = "mcp"
    API = "api"
    FILE = "file"
    APP = "app"
    DEVICE = "device"


class CapabilityGapStatus(str, Enum):
    NO_GAP = "no_gap"
    CAN_USE_EXISTING = "can_use_existing"
    CAN_USE_CONNECTOR = "can_use_connector"
    NEED_EXTENSION = "need_extension"
    NEED_HUMAN = "need_human"


class ExtensionStatus(str, Enum):
    PROPOSED = "proposed"
    SANDBOXED = "sandboxed"
    EVALUATED = "evaluated"
    PROMOTED = "promoted"
    REJECTED = "rejected"


class ApprovalStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TaskRunStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


def now_ts() -> float:
    return time.time()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass
class MemoryRecord:
    id: str
    kind: MemoryKind
    key: str
    value: Any
    confidence: float = 0.7
    source: str = "system"
    created_at: float = field(default_factory=now_ts)
    updated_at: float = field(default_factory=now_ts)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d


@dataclass
class ConnectorSpec:
    id: str
    name: str
    kind: ConnectorKind
    capabilities: List[str]
    risk_level: RiskLevel = RiskLevel.L1
    enabled: bool = True
    requires_approval: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CapabilityGap:
    id: str
    requested_goal: str
    required_capabilities: List[str]
    missing_capabilities: List[str]
    status: CapabilityGapStatus
    candidate_routes: List[str] = field(default_factory=list)
    candidate_connectors: List[str] = field(default_factory=list)
    extension_proposal_id: Optional[str] = None
    explanation: str = ""


@dataclass
class ExtensionProposal:
    id: str
    capability_name: str
    source_type: str
    source_ref: str
    risk_level: RiskLevel
    status: ExtensionStatus = ExtensionStatus.PROPOSED
    evaluation_score: float = 0.0
    promoted: bool = False
    rollback_plan: str = ""
    notes: List[str] = field(default_factory=list)


@dataclass
class ApprovalTicket:
    id: str
    goal: str
    action_summary: str
    risk_level: RiskLevel
    status: ApprovalStatus = ApprovalStatus.PENDING
    reason: str = ""
    created_at: float = field(default_factory=now_ts)
    resolved_at: Optional[float] = None


@dataclass
class TraceEvent:
    id: str
    run_id: str
    event_type: str
    message: str
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=now_ts)


@dataclass
class QualityReport:
    id: str
    run_id: str
    goal: str
    completeness: float
    safety: float
    usefulness: float
    efficiency: float
    final_score: float
    passed: bool
    issues: List[str] = field(default_factory=list)


@dataclass
class StrategyRule:
    id: str
    name: str
    condition: str
    action: str
    weight: float = 1.0
    enabled: bool = True
    updated_at: float = field(default_factory=now_ts)


@dataclass
class ContinuousTask:
    id: str
    title: str
    goal: str
    cadence: str
    status: TaskRunStatus = TaskRunStatus.CREATED
    last_run_at: Optional[float] = None
    next_run_hint: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AutonomyCycleResult:
    run_id: str
    goal: str
    status: TaskRunStatus
    memory_updates: int
    connector_matches: int
    capability_gap_status: CapabilityGapStatus
    approval_status: ApprovalStatus
    extension_status: Optional[ExtensionStatus]
    quality_score: float
    trace_events: int
    next_action: str
    details: Dict[str, Any] = field(default_factory=dict)
