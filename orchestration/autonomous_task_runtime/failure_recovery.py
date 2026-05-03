"""Failure recovery policy for autonomous pending-access task graphs."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping


@dataclass
class RecoveryDecision:
    recovered: bool
    strategy: str
    resume_from_checkpoint: bool
    requires_user: bool
    real_side_effect: bool
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FailureRecoveryPolicy:
    """Conservative recovery:
    - sandbox/tool transient failures may retry from checkpoint.
    - commit-barrier blocks are not failures; they become approval packets.
    - unknown failures pause and request review.
    """

    def decide(self, node: Mapping[str, Any], outcome: Mapping[str, Any]) -> RecoveryDecision:
        status = str(outcome.get("status") or "")
        semantic = (node.get("semantic") or {}).get("semantic_class") if isinstance(node.get("semantic"), Mapping) else None
        if status in {"dry_run_only", "sandbox_ready_authorized_non_commit", "sandbox_completed", "simulated"}:
            return RecoveryDecision(True, "no_recovery_needed", True, False, False, "node_completed_without_live_side_effect")
        if status == "commit_barrier_blocked" or semantic in {"payment", "signature", "external_send", "physical_actuation", "identity_commit", "destructive"}:
            return RecoveryDecision(True, "convert_to_approval_packet", True, True, False, "commit_action_paused_by_design")
        if status in {"transient_error", "timeout", "sandbox_error"}:
            return RecoveryDecision(True, "retry_once_from_checkpoint_then_pause", True, False, False, "recoverable_sandbox_failure")
        return RecoveryDecision(False, "pause_for_review", True, True, False, "unknown_failure_requires_human_review")
