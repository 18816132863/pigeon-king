from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict
import time
import uuid


def now_ts() -> float:
    return time.time()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class FabricStatus(str, Enum):
    READY = "ready"
    WARN = "warn"
    BLOCKED = "blocked"
    DEGRADED = "degraded"


class FabricGate(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class FabricSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FabricArtifact:
    id: str
    name: str
    kind: str
    status: FabricStatus
    score: float
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=now_ts)


@dataclass
class RuntimeFabricResult:
    run_id: str
    goal: str
    status: FabricStatus
    completed_versions: int
    artifact_count: int
    readiness_score: float
    gate: FabricGate
    severity: FabricSeverity
    dashboard_summary: str
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
