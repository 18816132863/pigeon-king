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


class CommandStatus(str, Enum):
    ACCEPTED = "accepted"
    ROUTED = "routed"
    REJECTED = "rejected"
    COMPLETED = "completed"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_APPROVAL = "waiting_approval"


class ScheduleStatus(str, Enum):
    CREATED = "created"
    DUE = "due"
    PAUSED = "paused"
    COMPLETED = "completed"


class DiagnosticStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class PackageStatus(str, Enum):
    CREATED = "created"
    EMPTY = "empty"
    FAILED = "failed"


class CompatibilityStatus(str, Enum):
    COMPATIBLE = "compatible"
    PARTIAL = "partial"
    INCOMPATIBLE = "incompatible"


class ActivationStatus(str, Enum):
    READY = "ready"
    DEGRADED_READY = "degraded_ready"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"


@dataclass
class RuntimeCommand:
    id: str
    raw_text: str
    intent: str
    priority: int
    risk_hint: str
    created_at: float = field(default_factory=now_ts)


@dataclass
class CommandResult:
    id: str
    command_id: str
    status: CommandStatus
    routed_to: str
    reason: str
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ApiRequest:
    id: str
    endpoint: str
    method: str
    body: Dict[str, Any]
    created_at: float = field(default_factory=now_ts)


@dataclass
class ApiResponse:
    id: str
    request_id: str
    status_code: int
    body: Dict[str, Any]


@dataclass
class JobRecord:
    id: str
    command_id: str
    title: str
    status: JobStatus
    attempts: int = 0
    max_attempts: int = 2
    result_summary: str = ""
    created_at: float = field(default_factory=now_ts)
    updated_at: float = field(default_factory=now_ts)


@dataclass
class ScheduleRecord:
    id: str
    title: str
    cadence: str
    status: ScheduleStatus
    next_run_hint: str
    linked_job_id: Optional[str] = None


@dataclass
class StateInspectionReport:
    id: str
    required_modules: Dict[str, bool]
    state_dirs: Dict[str, bool]
    cache_count: int
    status: DiagnosticStatus
    notes: List[str] = field(default_factory=list)


@dataclass
class DiagnosticReport:
    id: str
    checks: Dict[str, DiagnosticStatus]
    score: float
    status: DiagnosticStatus
    recommendations: List[str] = field(default_factory=list)


@dataclass
class PolicySimulationResult:
    id: str
    scenario: str
    expected: str
    actual: str
    passed: bool
    notes: List[str] = field(default_factory=list)


@dataclass
class ArtifactPackageRecord:
    id: str
    package_name: str
    files: List[str]
    status: PackageStatus
    command: str
    notes: List[str] = field(default_factory=list)


@dataclass
class CompatibilityReport:
    id: str
    layers: Dict[str, bool]
    status: CompatibilityStatus
    missing_layers: List[str]
    fallback_plan: str


@dataclass
class RuntimeActivationResult:
    run_id: str
    goal: str
    activation_status: ActivationStatus
    command_status: CommandStatus
    api_status_code: int
    job_status: JobStatus
    schedule_status: ScheduleStatus
    inspection_status: DiagnosticStatus
    diagnostic_status: DiagnosticStatus
    policy_passed: bool
    package_status: PackageStatus
    compatibility_status: CompatibilityStatus
    score: float
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
