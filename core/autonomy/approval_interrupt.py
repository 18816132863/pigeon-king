from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
from .schemas import ApprovalTicket, ApprovalStatus, RiskLevel, new_id, now_ts
from .storage import JsonStore


class ApprovalInterruptManager:
    """V91: approval and interrupt manager."""

    def __init__(self, root: str | Path = ".autonomy_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "approval_tickets.json")

    def required_for(self, risk_level: RiskLevel) -> bool:
        return risk_level in {RiskLevel.L3, RiskLevel.L4}

    def create_ticket(self, goal: str, action_summary: str, risk_level: RiskLevel, reason: str = "") -> ApprovalTicket:
        if not self.required_for(risk_level):
            return ApprovalTicket(
                id=new_id("approval"),
                goal=goal,
                action_summary=action_summary,
                risk_level=risk_level,
                status=ApprovalStatus.NOT_REQUIRED,
                reason=reason,
            )

        data = self.store.read([])
        ticket = ApprovalTicket(
            id=new_id("approval"),
            goal=goal,
            action_summary=action_summary,
            risk_level=risk_level,
            status=ApprovalStatus.PENDING,
            reason=reason or "High-risk or external side-effect action requires approval.",
        )
        data.append(self._to_dict(ticket))
        self.store.write(data)
        return ticket

    def resolve(self, ticket_id: str, approve: bool, reason: str = "") -> ApprovalTicket:
        data = self.store.read([])
        for item in data:
            if item["id"] == ticket_id:
                item["status"] = ApprovalStatus.APPROVED.value if approve else ApprovalStatus.REJECTED.value
                item["resolved_at"] = now_ts()
                if reason:
                    item["reason"] = reason
                self.store.write(data)
                return self._from_dict(item)
        raise KeyError(f"unknown ticket_id: {ticket_id}")

    def pending(self) -> List[ApprovalTicket]:
        return [self._from_dict(x) for x in self.store.read([]) if x.get("status") == ApprovalStatus.PENDING.value]

    def _to_dict(self, t: ApprovalTicket) -> Dict:
        return {
            "id": t.id,
            "goal": t.goal,
            "action_summary": t.action_summary,
            "risk_level": t.risk_level.value,
            "status": t.status.value,
            "reason": t.reason,
            "created_at": t.created_at,
            "resolved_at": t.resolved_at,
        }

    def _from_dict(self, item: Dict) -> ApprovalTicket:
        return ApprovalTicket(
            id=item["id"],
            goal=item["goal"],
            action_summary=item["action_summary"],
            risk_level=RiskLevel(item["risk_level"]),
            status=ApprovalStatus(item.get("status", ApprovalStatus.PENDING.value)),
            reason=item.get("reason", ""),
            created_at=float(item.get("created_at", now_ts())),
            resolved_at=item.get("resolved_at"),
        )
