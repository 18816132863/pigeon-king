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

class ToolMode(str, Enum):
    REAL = "real"
    DRY_RUN = "dry_run"
    APPROVAL_REQUIRED = "approval_required"
    BLOCKED = "blocked"

class ToolBindingStatus(str, Enum):
    BOUND = "bound"
    EXECUTED = "executed"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    FAILED = "failed"

@dataclass
class ToolBinding:
    id: str
    task_id: str
    task_title: str
    task_kind: str
    tool_name: str
    capability: str
    mode: ToolMode
    status: ToolBindingStatus
    risk_level: str
    reason: str
    checkpoint_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ToolExecutionResult:
    id: str
    binding_id: str
    task_id: str
    tool_name: str
    mode: ToolMode
    status: ToolBindingStatus
    output: Dict[str, Any]
    error: str = ""
    created_at: float = field(default_factory=now_ts)

@dataclass
class ToolBindingReport:
    id: str
    run_id: str
    checkpoint_id: str
    bindings: List[ToolBinding]
    results: List[ToolExecutionResult]
    mode_counts: Dict[str, int]
    tool_count: int
    real_count: int
    dry_run_count: int
    approval_count: int
    blocked_count: int
    final_status: str
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
