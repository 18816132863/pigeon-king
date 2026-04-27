"""
V25.2 Goal Contract V2

Turns a user request into a governable objective contract.
This is deliberately deterministic and schema-first so it can be tested and audited.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
import hashlib
import time


@dataclass
class GoalContractV2:
    goal_id: str
    user_intent: str
    objective: str
    constraints: List[str]
    priority: str
    deadline: Optional[str]
    risk_boundary: str
    information_sources: List[str]
    approval_points: List[str]
    done_definition: List[str]
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class GoalCompilerV2:
    def compile(
        self,
        user_intent: str,
        *,
        objective: Optional[str] = None,
        constraints: Optional[List[str]] = None,
        deadline: Optional[str] = None,
        information_sources: Optional[List[str]] = None,
    ) -> GoalContractV2:
        seed = f"{user_intent}|{deadline or ''}|{time.time_ns()}".encode("utf-8")
        goal_id = "goal_" + hashlib.sha256(seed).hexdigest()[:16]
        text = user_intent.strip()
        risk_boundary = "low_risk_auto_allowed"
        approval_points: List[str] = []
        lowered = text.lower()
        if any(word in lowered for word in ["delete", "payment", "transfer", "发送给别人", "删除", "支付", "转账"]):
            risk_boundary = "high_risk_requires_approval"
            approval_points.append("before_irreversible_or_external_side_effect")

        done_definition = [
            "all required actions have terminal status",
            "side effects have receipts or pending_verify markers",
            "result has been verified or explicitly classified",
            "memory writeback has been evaluated",
        ]

        return GoalContractV2(
            goal_id=goal_id,
            user_intent=text,
            objective=objective or text,
            constraints=constraints or [],
            priority="normal",
            deadline=deadline,
            risk_boundary=risk_boundary,
            information_sources=information_sources or ["current_context"],
            approval_points=approval_points,
            done_definition=done_definition,
        )
