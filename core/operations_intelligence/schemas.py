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


class IntelligenceStatus(str, Enum):
    READY = "ready"
    WARN = "warn"
    BLOCKED = "blocked"
    LEARNING = "learning"


class PriorityLevel(str, Enum):
    P0 = "P0_critical"
    P1 = "P1_high"
    P2 = "P2_medium"
    P3 = "P3_low"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReportLevel(str, Enum):
    TECHNICAL = "technical"
    OPERATOR = "operator"
    EXECUTIVE = "executive"


@dataclass
class VersionFeature:
    version: str
    name: str
    module: str
    status: IntelligenceStatus
    summary: str


@dataclass
class IntelligenceArtifact:
    id: str
    name: str
    kind: str
    status: IntelligenceStatus
    score: float
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=now_ts)


@dataclass
class OperationsIntelligenceResult:
    run_id: str
    goal: str
    status: IntelligenceStatus
    completed_versions: int
    artifact_count: int
    readiness_score: float
    risk_level: RiskLevel
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
