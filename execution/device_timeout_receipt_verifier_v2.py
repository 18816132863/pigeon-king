"""
V25.0 Device Timeout Receipt Verifier V2

Action timeout is not device offline. A timeout becomes:
- success_with_timeout_receipt if post verification proves the change happened
- timeout_pending_verify if verification is inconclusive
- failed_after_verify only when verification proves no change and no safe remedy exists
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


@dataclass
class VerifyOutcome:
    action_id: str
    device_status: str
    action_status: str
    reason: str
    verified: bool
    retry_allowed: bool


class DeviceTimeoutReceiptVerifierV2:
    def verify_after_timeout(
        self,
        *,
        action_id: str,
        action_name: str,
        device_connected: bool,
        verification_probe: Callable[[], Dict[str, Any]],
        expected: Dict[str, Any],
    ) -> VerifyOutcome:
        if not device_connected:
            return VerifyOutcome(
                action_id=action_id,
                device_status="device_offline",
                action_status="timeout_pending_verify",
                reason="device transport not connected; do not assume action result",
                verified=False,
                retry_allowed=False,
            )

        observed = verification_probe()
        if self._matches_expected(observed, expected):
            return VerifyOutcome(
                action_id=action_id,
                device_status="connected_but_action_timeout",
                action_status="success_with_timeout_receipt",
                reason=f"{action_name} timed out but post-verification matched expected state",
                verified=True,
                retry_allowed=False,
            )

        if observed.get("inconclusive"):
            return VerifyOutcome(
                action_id=action_id,
                device_status="connected_but_action_timeout",
                action_status="timeout_pending_verify",
                reason=f"{action_name} timed out and verification was inconclusive",
                verified=False,
                retry_allowed=False,
            )

        return VerifyOutcome(
            action_id=action_id,
            device_status="connected_but_action_timeout",
            action_status="failed_after_verify",
            reason=f"{action_name} timed out and post-verification did not match expected state",
            verified=True,
            retry_allowed=True,
        )

    def _matches_expected(self, observed: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        for key, value in expected.items():
            if observed.get(key) != value:
                return False
        return True
