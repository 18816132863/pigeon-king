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


class ConnectorKind(str, Enum):
    FILE = "file"
    MAIL_DRAFT = "mail_draft"
    CALENDAR_DRAFT = "calendar_draft"
    SAFE_SCRIPT = "safe_script"
    MODEL_ROUTE = "model_route"
    ACTION_BRIDGE = "action_bridge"
    DEVICE_PREPARE = "device_prepare"
    GENERIC = "generic"


class ConnectorMode(str, Enum):
    REAL = "real"
    DRAFT = "draft"
    DRY_RUN = "dry_run"
    APPROVAL_REQUIRED = "approval_required"
    BLOCKED = "blocked"


class ConnectorStatus(str, Enum):
    EXECUTED = "executed"
    DRAFTED = "drafted"
    PREPARED = "prepared"
    WAITING_APPROVAL = "waiting_approval"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class ConnectorExecution:
    id: str
    top_report_id: str
    tool_binding_id: str
    task_id: str
    task_title: str
    tool_name: str
    capability: str
    connector_kind: ConnectorKind
    mode: ConnectorMode
    status: ConnectorStatus
    checkpoint_id: str
    output: Dict[str, Any]
    error: str = ""
    created_at: float = field(default_factory=now_ts)


@dataclass
class ConnectorReport:
    id: str
    top_report_id: str
    message: str
    status: ConnectorStatus
    connector_count: int
    real_count: int
    draft_count: int
    dry_run_count: int
    approval_count: int
    blocked_count: int
    checkpoint_id: str
    executions: List[ConnectorExecution]
    final_report: Dict[str, Any]
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
