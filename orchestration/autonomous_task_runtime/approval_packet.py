"""Approval packet generation for blocked commit actions."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping

from governance.embodied_pending_state import CommitBarrier


@dataclass
class ApprovalPacket:
    packet_id: str
    status: str
    semantic_class: str
    risk_level: str
    blocked_action: Dict[str, Any]
    user_visible_summary: str
    required_unlock: str
    real_side_effect: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ApprovalPacketGenerator:
    def __init__(self) -> None:
        self.barrier = CommitBarrier()
        self._counter = 0

    def create(self, action: Mapping[str, Any] | None, reason: str | None = None) -> ApprovalPacket:
        self._counter += 1
        action = dict(action or {})
        barrier = self.barrier.check(action)
        semantic = barrier.semantic_class
        if semantic in {"payment", "signature", "physical_actuation", "identity_commit", "destructive"}:
            unlock = "blocked_until_explicit_dual_key_real_world_enablement"
        elif semantic == "external_send":
            unlock = "blocked_until_explicit_review_send_confirmation"
        else:
            unlock = "review_required_before_classification"
        return ApprovalPacket(
            packet_id=f"approval_packet_{self._counter:06d}",
            status="pending_user_review_no_live_execution",
            semantic_class=semantic,
            risk_level=barrier.risk_level,
            blocked_action=action,
            user_visible_summary=reason or barrier.reason,
            required_unlock=unlock,
            real_side_effect=False,
        )
