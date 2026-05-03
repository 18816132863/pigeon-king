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


class PreferenceStrength(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    HARD = "hard"


class FeedbackSignal(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    CORRECTION = "correction"


class DriftLevel(str, Enum):
    STABLE = "stable"
    WATCH = "watch"
    NEEDS_CONFIRMATION = "needs_confirmation"


class PersonalizationStatus(str, Enum):
    READY = "ready"
    LEARNING = "learning"
    NEEDS_CONFIRMATION = "needs_confirmation"
    BLOCKED = "blocked"


@dataclass
class UserProfile:
    id: str
    display_name: str
    working_style: str
    delivery_style: str
    risk_style: str
    language: str
    updated_at: float = field(default_factory=now_ts)
    confidence: float = 0.7


@dataclass
class PreferenceRule:
    id: str
    key: str
    value: Any
    strength: PreferenceStrength
    source: str
    confidence: float
    tags: List[str] = field(default_factory=list)
    updated_at: float = field(default_factory=now_ts)


@dataclass
class ProjectMemory:
    id: str
    name: str
    domain: str
    current_version: str
    goals: List[str]
    constraints: List[str]
    active: bool = True
    updated_at: float = field(default_factory=now_ts)


@dataclass
class RelationshipContext:
    id: str
    name: str
    role: str
    tone: str
    trust_level: str
    notes: List[str] = field(default_factory=list)
    updated_at: float = field(default_factory=now_ts)


@dataclass
class ProcedureTemplate:
    id: str
    name: str
    trigger_keywords: List[str]
    steps: List[str]
    success_count: int = 0
    failure_count: int = 0
    confidence: float = 0.6


@dataclass
class DecisionPattern:
    id: str
    scenario: str
    preferred_action: str
    avoided_action: str
    evidence: List[str]
    confidence: float


@dataclass
class FeedbackRecord:
    id: str
    signal: FeedbackSignal
    target: str
    message: str
    extracted_updates: Dict[str, Any]
    created_at: float = field(default_factory=now_ts)


@dataclass
class DriftGuardReport:
    id: str
    level: DriftLevel
    changed_keys: List[str]
    blocked_updates: List[str]
    allowed_updates: List[str]
    reason: str


@dataclass
class PersonalizationScorecard:
    id: str
    profile_score: float
    preference_score: float
    project_score: float
    procedure_score: float
    feedback_score: float
    final_score: float
    notes: List[str] = field(default_factory=list)


@dataclass
class PersonalizationResult:
    run_id: str
    goal: str
    status: PersonalizationStatus
    profile_name: str
    matched_preferences: int
    matched_projects: int
    matched_relationships: int
    selected_procedure: str
    decision_pattern: str
    feedback_updates: int
    drift_level: DriftLevel
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
