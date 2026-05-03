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


class FinalizerStatus(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class ShapeDimension(str, Enum):
    GOAL = "goal_kernel"
    MEMORY = "memory_kernel"
    JUDGE = "constitution_judge"
    WORLD = "world_interface"
    DAG = "task_graph"
    EXECUTION = "safe_execution"
    EXPANSION = "capability_expansion"
    RECOVERY = "checkpoint_recovery"
    LEARNING = "memory_writeback"
    GOLDEN = "golden_paths"


@dataclass
class ShapeCriterion:
    id: str
    dimension: ShapeDimension
    name: str
    passed: bool
    score: float
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GoldenPathCase:
    id: str
    name: str
    input_text: str
    expected_decision: str
    expected_status_contains: str
    must_have: List[str]


@dataclass
class GoldenPathResult:
    id: str
    case_name: str
    passed: bool
    score: float
    failures: List[str]
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FinalShapeReport:
    id: str
    status: FinalizerStatus
    final_score: float
    criteria: List[ShapeCriterion]
    golden_results: List[GoldenPathResult]
    main_entry: str
    next_action: str
    summary: str
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
