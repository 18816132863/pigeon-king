from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List
import time
import uuid

def now_ts() -> float:
    return time.time()

def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

class TopOperatorStatus(str, Enum):
    COMPLETED = "completed"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    FAILED = "failed"

@dataclass
class TopOperatorReport:
    id: str
    message: str
    status: TopOperatorStatus
    final_status: str
    goal_contract: Dict[str, Any]
    task_graph: Dict[str, Any]
    judge_decision: str
    risk_level: str
    tool_bindings: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    tool_mode_counts: Dict[str, int]
    auto_executed_tasks: List[str]
    approval_tasks: List[str]
    blocked_tasks: List[str]
    checkpoint_id: str
    action_log_count: int
    memory_writeback_count: int
    final_report: Dict[str, Any]
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
