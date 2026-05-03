"""
V26.1 — Universal Task Contract Schemas
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class IntentType(str, Enum):
    SEARCH = "search"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SUMMARIZE = "summarize"
    EXTRACT = "extract"
    SCHEDULE = "schedule"
    REMIND = "remind"
    DRAFT = "draft"
    SEND = "send"
    EXECUTE = "execute"
    VERIFY = "verify"
    RECOVER = "recover"
    READ = "read"


class ToolRole(str, Enum):
    PRIMARY_ACTION = "primary_action"
    SOURCE_SEARCH = "source_search"
    DEDUPE_CHECK = "dedupe_check"
    VALIDATION_CHECK = "validation_check"
    RECOVERY_CHECK = "recovery_check"


class ExecutionPolicy(str, Enum):
    REAL = "real"
    DRAFT = "draft"
    DRY_RUN = "dry_run"
    APPROVAL_REQUIRED = "approval_required"
    BLOCKED = "blocked"
    UNKNOWN_PENDING = "unknown_pending"


class RiskLevel(str, Enum):
    L1_LOW = "L1_low"
    L2_REVERSIBLE = "L2_reversible"
    L3_IRREVERSIBLE = "L3_irreversible"
    L4_HIGH = "L4_high"
    L5_CRITICAL = "L5_critical"


class StopCondition(str, Enum):
    SOURCE_UNCERTAIN = "source_uncertain"
    INTENT_MISMATCH = "intent_mismatch"
    HIGH_RISK_NO_APPROVAL = "high_risk_no_approval"
    SECRET_LEAK = "secret_leak"
    DATE_AMBIGUOUS = "date_ambiguous"
    NO_IDEMPOTENCY_KEY = "no_idempotency_key"
    TOOL_ROLE_UNCLEAR = "tool_role_unclear"
    TIMEOUT_NO_CHECKPOINT = "timeout_no_checkpoint"
    MUTUAL_CONTRADICTION = "mutual_contradiction"
    MISSING_PERMISSION = "missing_permission"


@dataclass
class SourceContract:
    """来源契约"""
    primary_source: str          # notes / calendar / alarm / gmail / file / user_input / device / web / local_workspace
    keywords: List[str] = field(default_factory=list)
    title_hint: str = ""
    date_hint: str = ""
    location_hint: str = ""
    person_hint: str = ""
    exclude_keywords: List[str] = field(default_factory=list)


@dataclass
class ActionContract:
    """动作契约"""
    actions: List[str] = field(default_factory=list)  # create_alarm, create_calendar_event, etc.
    tool_roles: Dict[str, ToolRole] = field(default_factory=dict)
    tool_name: str = ""


@dataclass
class IdempotencyKey:
    """幂等键"""
    source_id: str = ""
    action_type: str = ""
    date: str = ""
    time: str = ""
    title: str = ""
    target: str = ""

    @property
    def key(self) -> str:
        return f"{self.source_id}|{self.action_type}|{self.date}|{self.time}|{self.title}|{self.target}"


@dataclass
class CompletionCriteria:
    """完成标准"""
    must_have: List[str] = field(default_factory=list)
    evidence_required: List[str] = field(default_factory=list)
    min_matches: int = 1


@dataclass
class UniversalTaskContract:
    """通用任务契约"""
    goal: str = ""
    intent: IntentType = IntentType.SEARCH
    source: SourceContract = field(default_factory=SourceContract)
    action: ActionContract = field(default_factory=ActionContract)
    risk: RiskLevel = RiskLevel.L1_LOW
    execution_policy: ExecutionPolicy = ExecutionPolicy.REAL
    idempotency_key: IdempotencyKey = field(default_factory=IdempotencyKey)
    checkpoint_id: str = ""
    stop_conditions: List[StopCondition] = field(default_factory=list)
    completion_criteria: CompletionCriteria = field(default_factory=CompletionCriteria)
    timeout_policy: str = "async_job"  # async_job / sync / manual_review
    multi_source_merge: bool = False
    merged_sources: List[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "intent": self.intent.value if isinstance(self.intent, IntentType) else self.intent,
            "source": {
                "primary_source": self.source.primary_source,
                "keywords": self.source.keywords,
                "title_hint": self.source.title_hint,
                "date_hint": self.source.date_hint,
                "location_hint": self.source.location_hint,
                "person_hint": self.source.person_hint,
                "exclude_keywords": self.source.exclude_keywords,
            },
            "action": {
                "actions": self.action.actions,
                "tool_roles": {k: v.value for k, v in self.action.tool_roles.items()},
            },
            "risk": self.risk.value if isinstance(self.risk, RiskLevel) else self.risk,
            "execution_policy": self.execution_policy.value if isinstance(self.execution_policy, ExecutionPolicy) else self.execution_policy,
            "idempotency_key": {"key": self.idempotency_key.key},
            "checkpoint_id": self.checkpoint_id,
            "stop_conditions": [s.value if isinstance(s, StopCondition) else s for s in self.stop_conditions],
            "completion_criteria": {
                "must_have": self.completion_criteria.must_have,
                "evidence_required": self.completion_criteria.evidence_required,
                "min_matches": self.completion_criteria.min_matches,
            },
            "timeout_policy": self.timeout_policy,
            "multi_source_merge": self.multi_source_merge,
            "created_at": self.created_at,
        }


@dataclass
class ActionLogEntry:
    """动作日志条目"""
    tool_name: str
    action: str
    intent: str
    status: str  # created / skipped / duplicate / unknown_pending / approval_required / blocked / failed
    idempotency_key: str = ""
    source: str = ""
    result: str = ""
    checkpoint_id: str = ""
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class ExecutionReport:
    """执行报告"""
    goal: str = ""
    source_selected: str = ""
    source_evidence: List[str] = field(default_factory=list)
    task_graph: List[str] = field(default_factory=list)
    primary_actions: List[str] = field(default_factory=list)
    helper_actions: List[str] = field(default_factory=list)
    created_items: List[str] = field(default_factory=list)
    skipped_duplicates: List[str] = field(default_factory=list)
    unknown_pending: List[str] = field(default_factory=list)
    approval_required: List[str] = field(default_factory=list)
    blocked: List[str] = field(default_factory=list)
    failed: List[str] = field(default_factory=list)
    checkpoint_id: str = ""
    resume_entry: str = ""
    action_logs: List[ActionLogEntry] = field(default_factory=list)
    memory_writeback: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "source_selected": self.source_selected,
            "source_evidence": self.source_evidence,
            "task_graph": self.task_graph,
            "primary_actions": self.primary_actions,
            "helper_actions": self.helper_actions,
            "created_items": self.created_items,
            "skipped_duplicates": self.skipped_duplicates,
            "unknown_pending": self.unknown_pending,
            "approval_required": self.approval_required,
            "blocked": self.blocked,
            "failed": self.failed,
            "checkpoint_id": self.checkpoint_id,
            "resume_entry": self.resume_entry,
            "action_logs": [asdict(log) for log in self.action_logs],
            "memory_writeback": self.memory_writeback,
        }
