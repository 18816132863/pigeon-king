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


class EntryStatus(str, Enum):
    COMPLETED = "completed"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    FAILED = "failed"


class ActionLogStatus(str, Enum):
    RECORDED = "recorded"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    COMPLETED = "completed"


@dataclass
class RealWorkRequest:
    id: str
    message: str
    source: str
    user_id: str
    created_at: float = field(default_factory=now_ts)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionLogRecord:
    id: str
    request_id: str
    run_id: str
    task_id: str
    task_title: str
    status: ActionLogStatus
    judge_decision: str
    risk_level: str
    checkpoint_id: str
    summary: str
    evidence: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=now_ts)


@dataclass
class RealWorkReport:
    id: str
    request_id: str
    source: str
    status: EntryStatus
    final_status: str
    goal_contract: Dict[str, Any]
    task_graph: Dict[str, Any]
    judge_decision: str
    risk_level: str
    auto_executed_tasks: List[str]
    approval_tasks: List[str]
    blocked_tasks: List[str]
    checkpoint_id: str
    action_log_count: int
    memory_writeback_count: int
    final_result_report: Dict[str, Any]
    next_action: str
    created_at: float = field(default_factory=now_ts)


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
