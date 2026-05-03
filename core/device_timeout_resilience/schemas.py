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


class TimeoutStatus(str, Enum):
    PREPARED = "prepared"
    QUEUED = "queued"
    RUNNING = "running"
    HEARTBEAT_OK = "heartbeat_ok"
    WAITING_APPROVAL = "waiting_approval"
    PAUSED_BEFORE_TIMEOUT = "paused_before_timeout"
    RESUMABLE = "resumable"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class JobMode(str, Enum):
    FAST_ACK = "fast_ack"
    CHUNKED = "chunked"
    APPROVAL_WAIT = "approval_wait"
    DRY_RUN = "dry_run"


@dataclass
class TimeoutPolicy:
    hard_timeout_seconds: int = 60
    soft_deadline_seconds: int = 45
    heartbeat_interval_seconds: int = 10
    max_step_seconds: int = 35
    max_retries: int = 3
    pre_timeout_checkpoint_seconds: int = 50


@dataclass
class DeviceJobStep:
    id: str
    index: int
    title: str
    estimated_seconds: int
    status: TimeoutStatus
    checkpoint_id: str
    retry_count: int = 0
    output: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeviceJob:
    id: str
    message: str
    mode: JobMode
    status: TimeoutStatus
    estimated_seconds: int
    checkpoint_id: str
    approval_required: bool
    steps: List[DeviceJobStep]
    created_at: float = field(default_factory=now_ts)
    updated_at: float = field(default_factory=now_ts)


@dataclass
class Heartbeat:
    id: str
    job_id: str
    step_id: str
    status: TimeoutStatus
    checkpoint_id: str
    message: str
    created_at: float = field(default_factory=now_ts)


@dataclass
class TimeoutResilienceReport:
    id: str
    message: str
    status: TimeoutStatus
    policy: TimeoutPolicy
    job: DeviceJob
    heartbeats: List[Heartbeat]
    retry_plan: Dict[str, Any]
    elapsed_seconds: float
    no_blocking_call_over_soft_deadline: bool
    checkpoint_id: str
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
        elif hasattr(v, "__dataclass_fields__"):
            data[k] = to_dict(v)
    return data
