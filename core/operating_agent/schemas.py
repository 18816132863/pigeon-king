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


class RuleSeverity(str, Enum):
    INFO = "info"
    WARN = "warn"
    APPROVAL_REQUIRED = "approval_required"
    BLOCK = "block"


class DecisionStatus(str, Enum):
    ALLOW = "allow"
    APPROVAL_REQUIRED = "approval_required"
    BLOCK = "block"


class PermissionScope(str, Enum):
    READ = "read"
    WRITE = "write"
    EXTERNAL_SEND = "external_send"
    INSTALL = "install"
    PAYMENT = "payment"
    DEVICE_CONTROL = "device_control"
    SECRET_ACCESS = "secret_access"


class TrustLevel(str, Enum):
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    OFFICIAL = "official"


class ReleaseStage(str, Enum):
    DEV = "dev"
    CANARY = "canary"
    STABLE = "stable"
    BLOCKED = "blocked"


@dataclass
class ConstitutionRule:
    id: str
    name: str
    pattern: str
    severity: RuleSeverity
    reason: str
    enabled: bool = True
    tags: List[str] = field(default_factory=list)


@dataclass
class ConstitutionDecision:
    status: DecisionStatus
    matched_rules: List[str]
    reason: str
    required_permissions: List[PermissionScope] = field(default_factory=list)


@dataclass
class PermissionGrant:
    id: str
    subject: str
    scope: PermissionScope
    reason: str
    expires_at: Optional[float] = None
    created_at: float = field(default_factory=now_ts)
    revoked: bool = False


@dataclass
class ConnectorCandidate:
    id: str
    name: str
    capability: str
    source: str
    trust_level: TrustLevel
    score: float
    requires_permission: List[PermissionScope] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPServerSpec:
    id: str
    name: str
    endpoint: str
    allowed_tools: List[str]
    trust_level: TrustLevel
    enabled: bool = True
    handshake_ok: bool = False
    last_checked_at: Optional[float] = None


@dataclass
class PluginSandboxReport:
    id: str
    plugin_name: str
    source_ref: str
    static_safe: bool
    forbidden_hits: List[str]
    has_rollback: bool
    test_passed: bool
    promoted: bool
    score: float
    notes: List[str] = field(default_factory=list)


@dataclass
class SpecialistAgent:
    id: str
    name: str
    domains: List[str]
    model_group: str
    tools: List[str] = field(default_factory=list)
    priority: int = 50


@dataclass
class HandoffRecord:
    id: str
    goal: str
    from_agent: str
    to_agent: str
    reason: str
    payload: Dict[str, Any]
    status: str = "created"
    created_at: float = field(default_factory=now_ts)


@dataclass
class RecoveryEntry:
    id: str
    run_id: str
    action: str
    checkpoint: Dict[str, Any]
    rollback_plan: str
    reversible: bool
    created_at: float = field(default_factory=now_ts)


@dataclass
class BenchmarkCase:
    id: str
    name: str
    goal: str
    expected_status: DecisionStatus
    required_capabilities: List[str]
    risk_keywords: List[str] = field(default_factory=list)


@dataclass
class BenchmarkResult:
    id: str
    case_id: str
    passed: bool
    score: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReleaseGateResult:
    id: str
    stage: ReleaseStage
    passed: bool
    score: float
    gates: Dict[str, bool]
    blockers: List[str] = field(default_factory=list)


@dataclass
class OperatingCycleResult:
    run_id: str
    goal: str
    constitution_status: DecisionStatus
    permissions_ok: bool
    connector_count: int
    mcp_ready_count: int
    sandbox_promoted: bool
    handoff_agent: str
    recovery_entries: int
    benchmark_score: float
    release_stage: ReleaseStage
    final_status: str
    next_action: str
    details: Dict[str, Any] = field(default_factory=dict)


def dataclass_to_dict(obj: Any) -> Dict[str, Any]:
    data = asdict(obj)
    for k, v in list(data.items()):
        if isinstance(v, Enum):
            data[k] = v.value
        elif isinstance(v, list):
            data[k] = [x.value if isinstance(x, Enum) else x for x in v]
        elif isinstance(v, dict):
            data[k] = {kk: (vv.value if isinstance(vv, Enum) else vv) for kk, vv in v.items()}
    return data
