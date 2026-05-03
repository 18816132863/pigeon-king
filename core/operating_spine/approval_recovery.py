from __future__ import annotations

from pathlib import Path
from typing import Dict
from .schemas import ApprovalRecoveryPlan, ApprovalRecoveryStatus, new_id, to_dict
from .storage import JsonStore


class ApprovalRecoveryWorkflow:
    """V121: approval wait/resume/rollback workflow."""

    def __init__(self, root: str | Path = ".operating_spine_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "approval_recovery_plans.json")

    def build(self, action: str, requires_approval: bool) -> ApprovalRecoveryPlan:
        if not requires_approval:
            status = ApprovalRecoveryStatus.NOT_REQUIRED
            reason = "action does not require approval"
        else:
            status = ApprovalRecoveryStatus.WAITING
            reason = "approval required before side-effect execution"

        plan = ApprovalRecoveryPlan(
            id=new_id("approval_recovery"),
            action=action,
            status=status,
            checkpoint_id=new_id("checkpoint"),
            resume_command="python -S scripts/resume_from_checkpoint.py --checkpoint {checkpoint_id}",
            rollback_command="python -S scripts/rollback_checkpoint.py --checkpoint {checkpoint_id}",
            reason=reason,
        )
        self.store.append(to_dict(plan))
        return plan

    def mark_resumable(self, plan_id: str) -> ApprovalRecoveryPlan:
        data = self.store.read([])
        for item in data:
            if item["id"] == plan_id:
                item["status"] = ApprovalRecoveryStatus.RESUMABLE.value
                self.store.write(data)
                return self._from_dict(item)
        raise KeyError(f"unknown plan_id: {plan_id}")

    def _from_dict(self, item: Dict) -> ApprovalRecoveryPlan:
        return ApprovalRecoveryPlan(
            id=item["id"],
            action=item["action"],
            status=ApprovalRecoveryStatus(item["status"]),
            checkpoint_id=item["checkpoint_id"],
            resume_command=item["resume_command"],
            rollback_command=item["rollback_command"],
            reason=item["reason"],
        )
