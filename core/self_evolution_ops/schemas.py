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


class ContractStatus(str, Enum):
    READY = "ready"
    NEEDS_CLARIFICATION = "needs_clarification"
    UNSAFE = "unsafe"


class BudgetStatus(str, Enum):
    WITHIN_BUDGET = "within_budget"
    NEEDS_DOWNGRADE = "needs_downgrade"
    BLOCKED_OVER_BUDGET = "blocked_over_budget"


class PrivacyLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    SECRET = "secret"


class CircuitStatus(str, Enum):
    CLOSED = "closed"
    HALF_OPEN = "half_open"
    OPEN = "open"


class SimulationStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class DriftStatus(str, Enum):
    STABLE = "stable"
    WATCH = "watch"
    DRIFTING = "drifting"


class ImprovementStatus(str, Enum):
    PROPOSED = "proposed"
    SAFE_TO_APPLY = "safe_to_apply"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


@dataclass
class IntentContract:
    id: str
    goal: str
    objective: str
    acceptance_criteria: List[str]
    constraints: List[str]
    non_goals: List[str]
    risk_notes: List[str]
    status: ContractStatus
    created_at: float = field(default_factory=now_ts)


@dataclass
class ContextPack:
    id: str
    goal: str
    selected_context: List[Dict[str, Any]]
    omitted_context: List[str]
    confidence: float
    token_estimate: int
    created_at: float = field(default_factory=now_ts)


@dataclass
class ReliabilityDecision:
    tool_name: str
    circuit_status: CircuitStatus
    max_retries: int
    retry_allowed: bool
    fallback_tool: Optional[str]
    reason: str


@dataclass
class BudgetDecision:
    id: str
    task_type: str
    token_budget: int
    cost_budget: float
    time_budget_seconds: int
    status: BudgetStatus
    recommended_model_group: str
    reason: str


@dataclass
class RedactionReport:
    id: str
    privacy_level: PrivacyLevel
    original_length: int
    redacted_length: int
    replacements: Dict[str, int]
    safe_text: str


@dataclass
class FallbackPlan:
    id: str
    unavailable_capability: str
    fallback_mode: str
    steps: List[str]
    quality_expected: float
    needs_user_notice: bool


@dataclass
class SimulationResult:
    id: str
    scenario: str
    status: SimulationStatus
    score: float
    failures: List[str]
    recommendations: List[str]


@dataclass
class DriftReport:
    id: str
    status: DriftStatus
    drift_score: float
    changed_preferences: List[str]
    suggested_actions: List[str]


@dataclass
class ObservabilityReport:
    id: str
    runs: int
    success_rate: float
    avg_quality: float
    budget_violations: int
    privacy_events: int
    open_circuits: int
    summary: str


@dataclass
class ImprovementPlan:
    id: str
    title: str
    status: ImprovementStatus
    target_modules: List[str]
    proposed_changes: List[str]
    expected_gain: float
    risk_level: str
    rollback_plan: str


@dataclass
class SelfEvolutionCycleResult:
    run_id: str
    goal: str
    contract_status: ContractStatus
    context_confidence: float
    budget_status: BudgetStatus
    privacy_level: PrivacyLevel
    reliability_status: CircuitStatus
    fallback_mode: str
    simulation_status: SimulationStatus
    drift_status: DriftStatus
    observability_summary: str
    improvement_status: ImprovementStatus
    final_status: str
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
