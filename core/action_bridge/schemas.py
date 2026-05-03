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


class ActionKind(str, Enum):
    READ = "read"
    WRITE = "write"
    SEND = "send"
    DELETE = "delete"
    INSTALL = "install"
    PAY = "pay"
    DEVICE_CONTROL = "device_control"
    MEDIA_GENERATE = "media_generate"
    PLAN_ONLY = "plan_only"


class ActionRisk(str, Enum):
    L0 = "L0_readonly"
    L1 = "L1_low"
    L2 = "L2_reversible"
    L3 = "L3_external_side_effect"
    L4 = "L4_sensitive_or_irreversible"


class ActionStatus(str, Enum):
    COMPILED = "compiled"
    DRY_RUN = "dry_run"
    WAITING_APPROVAL = "waiting_approval"
    EXECUTED = "executed"
    BLOCKED = "blocked"
    FAILED = "failed"


class DeviceStatus(str, Enum):
    UNKNOWN = "unknown"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    DISCONNECTED = "disconnected"


class AdapterStatus(str, Enum):
    ACTIVE = "active"
    DISABLED = "disabled"
    MISSING = "missing"


class EvidenceKind(str, Enum):
    INPUT = "input"
    DECISION = "decision"
    DRY_RUN = "dry_run"
    OUTPUT = "output"
    APPROVAL = "approval"
    ERROR = "error"


class NotificationLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ACTION_REQUIRED = "action_required"
    CRITICAL = "critical"


class HandoffStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class BackgroundRunStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


class BridgeStatus(str, Enum):
    READY = "ready"
    DRY_RUN_READY = "dry_run_ready"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"


@dataclass
class ActionSpec:
    id: str
    goal: str
    kind: ActionKind
    risk: ActionRisk
    target: str
    parameters: Dict[str, Any]
    reversible: bool
    requires_approval: bool
    status: ActionStatus = ActionStatus.COMPILED


@dataclass
class DeviceSession:
    id: str
    device_name: str
    status: DeviceStatus
    capabilities: List[str]
    last_seen_at: float = field(default_factory=now_ts)
    notes: List[str] = field(default_factory=list)


@dataclass
class ToolAdapterSpec:
    id: str
    name: str
    capability: str
    status: AdapterStatus
    risk_limit: ActionRisk
    dry_run_supported: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvidenceRecord:
    id: str
    run_id: str
    kind: EvidenceKind
    title: str
    content: Dict[str, Any]
    created_at: float = field(default_factory=now_ts)


@dataclass
class GuardedExecutionResult:
    id: str
    action_id: str
    status: ActionStatus
    dry_run: bool
    executed: bool
    reason: str
    rollback_hint: str
    output: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NotificationRecord:
    id: str
    level: NotificationLevel
    title: str
    message: str
    action_required: bool
    created_at: float = field(default_factory=now_ts)


@dataclass
class HandoffItem:
    id: str
    title: str
    reason: str
    action_id: str
    status: HandoffStatus
    options: List[str]
    created_at: float = field(default_factory=now_ts)


@dataclass
class BackgroundRunRecord:
    id: str
    title: str
    status: BackgroundRunStatus
    checkpoint: Dict[str, Any]
    resume_hint: str
    created_at: float = field(default_factory=now_ts)


@dataclass
class RealWorldScenarioResult:
    id: str
    scenario: str
    passed: bool
    score: float
    checks: Dict[str, bool]
    failures: List[str] = field(default_factory=list)


@dataclass
class ActionBridgeResult:
    run_id: str
    goal: str
    bridge_status: BridgeStatus
    action_kind: ActionKind
    action_risk: ActionRisk
    device_status: DeviceStatus
    adapter_status: AdapterStatus
    execution_status: ActionStatus
    notification_level: NotificationLevel
    handoff_status: Optional[HandoffStatus]
    background_status: BackgroundRunStatus
    scenario_score: float
    evidence_count: int
    next_action: str
    details: Dict[str, Any] = field(default_factory=dict)


def to_dict(obj: Any) -> Dict[str, Any]:
    data = asdict(obj)
    for k, v in list(data.items()):
        if isinstance(v, Enum):
            data[k] = v.value
        elif isinstance(v, list):
            data[k] = [x.value if isinstance(x, Enum) else (to_dict(x) if hasattr(x, "__dataclass_fields__") else x) for x in v]
        elif isinstance(v, dict):
            data[k] = {kk: (vv.value if isinstance(vv, Enum) else vv) for kk, vv in v.items()}
    return data
