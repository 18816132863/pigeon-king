"""
V24.4 Remediation Planner.

Layer: L3 Orchestration.

Maps classified failures to safe next steps.  It does not execute the steps.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ARCHITECTURE_LAYER = "L3 Orchestration"


@dataclass(frozen=True)
class RemediationPlan:
    action: str
    steps: list[str]
    can_auto_continue: bool
    must_avoid: list[str]
    reason: str


def plan_remediation(classification: Any, context: dict[str, Any] | None = None) -> RemediationPlan:
    context = context or {}
    code = getattr(classification, "code", str(classification))

    if code == "ACTION_TIMEOUT":
        return RemediationPlan(
            action="verify_then_continue",
            steps=[
                "run targeted search/read of current device state",
                "compare observed state with expected state",
                "if matched, mark success_with_timeout_receipt",
                "if not matched, choose GUI fallback or ask user depending on risk",
            ],
            can_auto_continue=True,
            must_avoid=[
                "do_not_mark_device_offline",
                "do_not_blindly_retry_modify_alarm",
                "do_not_duplicate_create_alarm_or_push",
            ],
            reason="timeout may be receipt-only; verification is safer than retry",
        )

    if code == "DEVICE_OFFLINE":
        return RemediationPlan(
            action="defer_until_online",
            steps=["mark workflow pending_device_online", "write heartbeat state", "resume when transport is online"],
            can_auto_continue=False,
            must_avoid=["do_not_retry_in_loop", "do_not_call_gui_fallback_without_device"],
            reason="transport unavailable",
        )

    if code == "VALIDATION_ERROR":
        return RemediationPlan(
            action="fix_arguments",
            steps=["inspect required schema", "repair arguments", "rerun only the failed validation step"],
            can_auto_continue=True,
            must_avoid=["do_not_execute_with_missing_entityId"],
            reason="invalid args are deterministic and must be fixed before execution",
        )

    if code == "POLICY_BLOCK":
        return RemediationPlan(
            action="request_confirmation_or_stop",
            steps=["surface concise approval summary", "wait for confirmation", "resume from pending step only"],
            can_auto_continue=False,
            must_avoid=["do_not_bypass_governance"],
            reason="governance must remain authoritative",
        )

    return RemediationPlan(
        action="collect_evidence",
        steps=["collect trace", "classify again", "prefer verification over retry"],
        can_auto_continue=False,
        must_avoid=["do_not_guess_success", "do_not_repeat_side_effects"],
        reason="unknown failures require evidence",
    )
