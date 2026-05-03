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


class CheckStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class ProfileName(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    CANARY = "canary"
    PROD = "prod"


class GateStatus(str, Enum):
    OPEN = "open"
    WARN = "warn"
    CLOSED = "closed"


class SnapshotStatus(str, Enum):
    CREATED = "created"
    EMPTY = "empty"
    FAILED = "failed"


class RegressionStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class ReleaseStatus(str, Enum):
    READY = "ready"
    DEGRADED_READY = "degraded_ready"
    BLOCKED = "blocked"


@dataclass
class EnvironmentCheck:
    id: str
    python_version: str
    cwd: str
    pycache_count: int
    required_dirs: Dict[str, bool]
    status: CheckStatus
    notes: List[str] = field(default_factory=list)


@dataclass
class ConfigContract:
    id: str
    required_env: List[str]
    optional_env: List[str]
    present_required: List[str]
    missing_required: List[str]
    status: CheckStatus
    notes: List[str] = field(default_factory=list)


@dataclass
class DependencyCheck:
    id: str
    module_name: str
    available: bool
    source: str
    status: CheckStatus
    notes: List[str] = field(default_factory=list)


@dataclass
class SnapshotRecord:
    id: str
    root: str
    tracked_files: int
    manifest_path: str
    status: SnapshotStatus
    created_at: float = field(default_factory=now_ts)


@dataclass
class RollbackPlan:
    id: str
    snapshot_id: str
    reversible: bool
    commands: List[str]
    notes: List[str] = field(default_factory=list)


@dataclass
class RegressionCase:
    id: str
    name: str
    category: str
    expected: str
    actual: str
    passed: bool
    notes: List[str] = field(default_factory=list)


@dataclass
class RegressionSuiteResult:
    id: str
    total: int
    passed: int
    failed: int
    status: RegressionStatus
    cases: List[RegressionCase] = field(default_factory=list)


@dataclass
class ReleaseManifest:
    id: str
    version_from: str
    version_to: str
    modules: List[str]
    scripts: List[str]
    tests: List[str]
    docs: List[str]
    status: CheckStatus


@dataclass
class DeploymentProfile:
    id: str
    name: ProfileName
    allowed_risk: str
    require_approval: bool
    require_snapshot: bool
    require_regression_pass: bool
    gate_status: GateStatus
    notes: List[str] = field(default_factory=list)


@dataclass
class RuntimeReport:
    id: str
    release_id: str
    status: ReleaseStatus
    checks: Dict[str, str]
    score: float
    summary: str


@dataclass
class ReleaseHardeningResult:
    run_id: str
    goal: str
    release_status: ReleaseStatus
    env_status: CheckStatus
    config_status: CheckStatus
    dependency_status: CheckStatus
    snapshot_status: SnapshotStatus
    regression_status: RegressionStatus
    deployment_gate: GateStatus
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
