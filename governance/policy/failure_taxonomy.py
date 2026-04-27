"""
V24.3 Failure Taxonomy.

Layer: L5 Governance.

Classifies failures without collapsing action timeout into device offline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ARCHITECTURE_LAYER = "L5 Governance"


@dataclass(frozen=True)
class FailureClassification:
    code: str
    severity: str
    device_state: str
    safe_to_retry: bool
    requires_verification: bool
    explanation: str


def classify_failure(event: dict[str, Any]) -> FailureClassification:
    raw = str(event.get("error") or event.get("status") or event.get("code") or "").lower()
    action = str(event.get("action") or event.get("tool") or "")

    if raw in {"timeout", "receipt_timeout", "action_timeout"}:
        return FailureClassification(
            code="ACTION_TIMEOUT",
            severity="medium",
            device_state="connected_but_action_timeout",
            safe_to_retry=False,
            requires_verification=True,
            explanation=f"{action} timed out; verify state before retrying.",
        )

    if raw in {"device_offline", "transport_unavailable", "no_device"}:
        return FailureClassification(
            code="DEVICE_OFFLINE",
            severity="high",
            device_state="offline",
            safe_to_retry=False,
            requires_verification=False,
            explanation="Device transport is unavailable; defer until online.",
        )

    if raw in {"policy_denied", "blocked", "requires_confirmation"}:
        return FailureClassification(
            code="POLICY_BLOCK",
            severity="high",
            device_state="unchanged",
            safe_to_retry=False,
            requires_verification=False,
            explanation="Governance blocked the action or requires confirmation.",
        )

    if raw in {"validation_error", "bad_args", "missing_entityid"}:
        return FailureClassification(
            code="VALIDATION_ERROR",
            severity="medium",
            device_state="connected",
            safe_to_retry=False,
            requires_verification=False,
            explanation="Tool arguments are invalid; fix args before execution.",
        )

    return FailureClassification(
        code="UNKNOWN",
        severity="medium",
        device_state="unknown",
        safe_to_retry=False,
        requires_verification=True,
        explanation="Unknown failure; collect evidence and verify before retry.",
    )
