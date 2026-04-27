"""
V24.0 Side Effect Transaction.

Layer: L3 Orchestration.

Represents multi-channel side effects as a transaction.  It supports partial
success states so one slow device action does not hide successful push/cron
results.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any
import time


ARCHITECTURE_LAYER = "L3 Orchestration"

SUCCESS_STATUSES = {"success", "scheduled", "success_with_timeout_receipt"}
PENDING_STATUSES = {"reserved", "running", "timeout_pending_verify", "pending", "pending_verify"}
FAILED_STATUSES = {"failed", "failed_device_offline", "failed_unknown", "policy_denied"}


@dataclass
class TransactionStep:
    name: str
    status: str = "pending"
    layer: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)


@dataclass
class SideEffectTransaction:
    transaction_id: str
    goal: str
    steps: list[TransactionStep]
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def update_step(self, name: str, status: str, evidence: dict[str, Any] | None = None) -> None:
        for step in self.steps:
            if step.name == name:
                step.status = status
                step.evidence = evidence or {}
                step.updated_at = time.time()
                self.updated_at = time.time()
                return
        raise KeyError(f"unknown step: {name}")

    def overall_status(self) -> str:
        statuses = [step.status for step in self.steps]
        if all(status in SUCCESS_STATUSES for status in statuses):
            return "success"
        if any(status in FAILED_STATUSES for status in statuses) and any(status in SUCCESS_STATUSES for status in statuses):
            return "partial_success"
        if any(status in PENDING_STATUSES for status in statuses):
            return "pending_or_partial"
        if all(status in FAILED_STATUSES for status in statuses):
            return "failed"
        return "mixed"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_three_channel_reminder_transaction(transaction_id: str, goal: str) -> SideEffectTransaction:
    return SideEffectTransaction(
        transaction_id=transaction_id,
        goal=goal,
        steps=[
            TransactionStep(name="alarm", layer="L4 Execution"),
            TransactionStep(name="hiboard_push", layer="L4 Execution"),
            TransactionStep(name="chat_cron", layer="L4 Execution"),
            TransactionStep(name="final_verify", layer="L3 Orchestration"),
        ],
    )
