"""Commit barrier: the final hard stop before real-world side effects."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Optional

from .action_semantics import classify_action_semantics
from .freeze_switch import get_live_access_state


@dataclass(frozen=True)
class CommitBarrierResult:
    allowed: bool
    mode: str
    semantic_class: str
    risk_level: str
    is_commit_action: bool
    hard_stop: bool
    real_side_effect_allowed: bool
    stopped_at: str
    reason: str
    next_safe_action: str
    review_required: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CommitBarrier:
    """Default barrier for the target state described in the report.

    It allows observation, reasoning, generation, simulation and preparation.
    It blocks external sends and hard-stops payment/signature/physical/destructive actions.
    """

    def check(
        self,
        action: Mapping[str, Any] | None,
        *,
        config: Optional[Mapping[str, Any]] = None,
        authorization: Optional[Mapping[str, Any]] = None,
    ) -> CommitBarrierResult:
        semantic = classify_action_semantics(action)
        live = get_live_access_state(config)

        if semantic.allowed_in_pending_access_state:
            return CommitBarrierResult(
                allowed=True,
                mode="pending_access_non_commit_allowed",
                semantic_class=semantic.semantic_class,
                risk_level=semantic.risk_level,
                is_commit_action=False,
                hard_stop=False,
                real_side_effect_allowed=False,
                stopped_at="not_applicable",
                reason=semantic.reason,
                next_safe_action="execute_in_sandbox_or_prepare_output",
                review_required=False,
            )

        if semantic.is_commit_action:
            if semantic.hard_stop:
                reason = "hard_cutoff_payment_signature_physical_or_destructive_action"
                next_safe = "convert_to_mock_preview_or_approval_pack_without_live_execution"
            else:
                reason = "external_commit_requires_manual_review_in_pending_access_state"
                next_safe = "create_draft_or_pending_outbox_item_only"
            return CommitBarrierResult(
                allowed=False,
                mode="commit_blocked_pending_access_state",
                semantic_class=semantic.semantic_class,
                risk_level=semantic.risk_level,
                is_commit_action=True,
                hard_stop=semantic.hard_stop,
                real_side_effect_allowed=False,
                stopped_at="commit_barrier",
                reason=reason,
                next_safe_action=next_safe,
                review_required=True,
            )

        return CommitBarrierResult(
            allowed=False,
            mode="unclassified_action_blocked_for_review",
            semantic_class=semantic.semantic_class,
            risk_level=semantic.risk_level,
            is_commit_action=False,
            hard_stop=False,
            real_side_effect_allowed=False,
            stopped_at="semantic_classifier",
            reason="unknown_action_requires_review_before_any_execution",
            next_safe_action="ask_for_classification_or_run_probe_only",
            review_required=True,
        )


def enforce_commit_barrier(action: Mapping[str, Any] | None, **kwargs: Any) -> Dict[str, Any]:
    return CommitBarrier().check(action, **kwargs).to_dict()
