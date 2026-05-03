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


class EventSeverity(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    CRITICAL = "critical"


class MigrationStatus(str, Enum):
    NOT_NEEDED = "not_needed"
    PLANNED = "planned"
    APPLIED = "applied"
    FAILED = "failed"


class CapabilityContractStatus(str, Enum):
    ACTIVE = "active"
    MISSING = "missing"
    DEGRADED = "degraded"
    DISABLED = "disabled"


class RuntimeNodeStatus(str, Enum):
    READY = "ready"
    SKIPPED = "skipped"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


class ApprovalRecoveryStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    WAITING = "waiting"
    RESUMABLE = "resumable"
    REJECTED = "rejected"


class ConnectorHealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class MemoryConsolidationStatus(str, Enum):
    COMPACTED = "compacted"
    NOOP = "noop"
    NEEDS_REVIEW = "needs_review"


class SkillLifecycleStatus(str, Enum):
    PROPOSED = "proposed"
    CANARY = "canary"
    ACTIVE = "active"
    ROLLED_BACK = "rolled_back"
    DISABLED = "disabled"


class ScenarioStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class SpineStatus(str, Enum):
    READY = "ready"
    WAITING_APPROVAL = "waiting_approval"
    DEGRADED_READY = "degraded_ready"
    BLOCKED = "blocked"


@dataclass
class SpineEvent:
    id: str
    run_id: str
    topic: str
    severity: EventSeverity
    message: str
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=now_ts)


@dataclass
class MigrationRecord:
    id: str
    from_version: str
    to_version: str
    status: MigrationStatus
    files_checked: List[str]
    actions: List[str]
    rollback_hint: str
    created_at: float = field(default_factory=now_ts)


@dataclass
class CapabilityContract:
    id: str
    name: str
    provider_module: str
    required_methods: List[str]
    status: CapabilityContractStatus
    missing_methods: List[str] = field(default_factory=list)
    fallback: Optional[str] = None


@dataclass
class RuntimeNodeResult:
    id: str
    node_name: str
    status: RuntimeNodeStatus
    selected_capability: str
    risk_level: str
    output_summary: str
    next_nodes: List[str] = field(default_factory=list)


@dataclass
class ApprovalRecoveryPlan:
    id: str
    action: str
    status: ApprovalRecoveryStatus
    checkpoint_id: str
    resume_command: str
    rollback_command: str
    reason: str


@dataclass
class ConnectorHealthReport:
    id: str
    connector_name: str
    status: ConnectorHealthStatus
    latency_ms: int
    failure_rate: float
    recommendation: str


@dataclass
class MemoryConsolidationReport:
    id: str
    status: MemoryConsolidationStatus
    before_count: int
    after_count: int
    summary_keys: List[str]
    review_notes: List[str] = field(default_factory=list)


@dataclass
class SkillLifecycleRecord:
    id: str
    skill_name: str
    status: SkillLifecycleStatus
    version: str
    canary_score: float
    rollback_plan: str
    notes: List[str] = field(default_factory=list)


@dataclass
class ScenarioResult:
    id: str
    scenario_name: str
    status: ScenarioStatus
    score: float
    checks: Dict[str, bool]
    failures: List[str] = field(default_factory=list)


@dataclass
class OperatingSpineResult:
    run_id: str
    goal: str
    status: SpineStatus
    events: int
    migrations: int
    active_contracts: int
    runtime_nodes: int
    approval_status: ApprovalRecoveryStatus
    healthy_connectors: int
    memory_status: MemoryConsolidationStatus
    active_skills: int
    scenario_score: float
    next_action: str
    details: Dict[str, Any] = field(default_factory=dict)


def to_dict(obj: Any) -> Dict[str, Any]:
    data = asdict(obj)
    for k, v in list(data.items()):
        if isinstance(v, Enum):
            data[k] = v.value
        elif isinstance(v, list):
            data[k] = [x.value if isinstance(x, Enum) else x for x in v]
        elif isinstance(v, dict):
            data[k] = {kk: (vv.value if isinstance(vv, Enum) else vv) for kk, vv in v.items()}
    return data
