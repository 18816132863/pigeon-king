"""V50.0 Human Approval Interrupt V5.

Durable human-in-the-loop approvals. High-risk actions are paused with an approval
packet and resumed only with explicit approved status.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional
from datetime import datetime, timezone
import uuid

@dataclass
class ApprovalPacketV5:
    approval_id: str
    risk_tier: str
    action_summary: str
    status: str
    resume_token: str
    created_at: str
    payload: Dict[str, Any]

class HumanApprovalInterruptV5:
    def create(self, risk_tier: str, action_summary: str, payload: Optional[Dict[str, Any]] = None) -> ApprovalPacketV5:
        approval_id = "approval_" + uuid.uuid4().hex[:12]
        return ApprovalPacketV5(
            approval_id=approval_id,
            risk_tier=risk_tier,
            action_summary=action_summary,
            status="waiting_for_approval",
            resume_token="resume_" + uuid.uuid4().hex[:16],
            created_at=datetime.now(timezone.utc).isoformat(),
            payload=payload or {},
        )

    def resume(self, packet: ApprovalPacketV5, decision: str) -> Dict[str, Any]:
        if decision not in {"approved", "denied"}:
            raise ValueError("decision must be approved or denied")
        return {"approval_id": packet.approval_id, "resume_token": packet.resume_token, "status": decision, "can_continue": decision == "approved"}

    @staticmethod
    def to_dict(packet: ApprovalPacketV5) -> Dict[str, Any]:
        return asdict(packet)
