"""
V23.8 Device Receipt Reconciler.

Layer: L4 Execution.

Important rule:
A device action timeout is NOT the same as device offline.  For alarm modify,
a timeout may mean the action completed but the receipt did not return.
The reconciler performs post-timeout verification and returns a precise status.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ARCHITECTURE_LAYER = "L4 Execution"


@dataclass(frozen=True)
class ReconcileResult:
    status: str
    device_state: str
    reason: str
    verified: bool
    next_action: str | None = None
    evidence: dict[str, Any] | None = None


def expected_alarm_matches(expected: dict[str, Any], observed: dict[str, Any] | None) -> bool:
    if not observed:
        return False
    checks = []
    if expected.get("entityId") is not None:
        checks.append(str(observed.get("entityId")) == str(expected.get("entityId")))
    if expected.get("alarmTitle") is not None:
        checks.append(str(observed.get("alarmTitle")) == str(expected.get("alarmTitle")))
    if expected.get("alarmTime") is not None:
        checks.append(str(observed.get("alarmTime")) == str(expected.get("alarmTime")))
    if expected.get("daysOfWakeType") is not None:
        checks.append(str(observed.get("daysOfWakeType")) == str(expected.get("daysOfWakeType")))
    return bool(checks) and all(checks)


def reconcile_device_action(
    *,
    action_name: str,
    action_result: dict[str, Any] | None,
    expected_state: dict[str, Any],
    observed_after_timeout: dict[str, Any] | None,
) -> ReconcileResult:
    """Reconcile a tool result and verification observation."""
    if action_result and action_result.get("ok") is True:
        return ReconcileResult(
            status="success",
            device_state="connected",
            reason="tool returned ok",
            verified=True,
            evidence={"action_result": action_result},
        )

    error = (action_result or {}).get("error") or (action_result or {}).get("status")
    if error in {"device_offline", "transport_unavailable"}:
        return ReconcileResult(
            status="failed_device_offline",
            device_state="offline",
            reason=str(error),
            verified=False,
            next_action="defer_until_device_online",
            evidence={"action_result": action_result},
        )

    if error in {"timeout", "receipt_timeout", "action_timeout"} or action_result is None:
        if expected_alarm_matches(expected_state, observed_after_timeout):
            return ReconcileResult(
                status="success_with_timeout_receipt",
                device_state="connected_but_action_timeout",
                reason="timeout receipt but post verification matched expected state",
                verified=True,
                evidence={"observed_after_timeout": observed_after_timeout},
            )
        return ReconcileResult(
            status="timeout_pending_verify",
            device_state="connected_but_action_timeout",
            reason="device action timed out and post verification did not yet prove success",
            verified=False,
            next_action="search_again_or_gui_fallback",
            evidence={"observed_after_timeout": observed_after_timeout},
        )

    return ReconcileResult(
        status="failed_unknown",
        device_state="connected",
        reason=f"unknown tool outcome: {error}",
        verified=False,
        next_action="classify_failure",
        evidence={"action_result": action_result, "observed_after_timeout": observed_after_timeout},
    )


class DeviceReceiptReconciler:
    """向后兼容的 DeviceReceiptReconciler 包装类。

    纯本地执行，无外部 API，无真实副作用。
    """

    def __init__(self):
        self.last_result: ReconcileResult | None = None

    def reconcile(
        self,
        action_name: str,
        action_result: dict[str, Any] | None,
        expected_state: dict[str, Any],
        observed_after_timeout: dict[str, Any] | None = None,
    ) -> ReconcileResult:
        self.last_result = reconcile_device_action(
            action_name=action_name,
            action_result=action_result,
            expected_state=expected_state,
            observed_after_timeout=observed_after_timeout,
        )
        return self.last_result

    def __call__(
        self,
        action_name: str,
        action_result: dict[str, Any] | None,
        expected_state: dict[str, Any],
        observed_after_timeout: dict[str, Any] | None = None,
    ) -> ReconcileResult:
        return self.reconcile(action_name, action_result, expected_state, observed_after_timeout)
