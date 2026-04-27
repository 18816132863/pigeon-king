"""
V23.4 Device Action Timeout Verifier.

Fixes the common false failure pattern:
- the device is connected
- a device action times out waiting for receipt
- the action may actually have completed on the device

The verifier converts action timeout into a pending verification state instead of
marking the device offline.  It is especially important for alarm modify flows.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Callable, Dict, Optional


class DeviceActionState(str, Enum):
    SUCCESS = "success"
    SUCCESS_WITH_TIMEOUT_RECEIPT = "success_with_timeout_receipt"
    CONNECTED_BUT_ACTION_TIMEOUT = "connected_but_action_timeout"
    TIMEOUT_PENDING_VERIFY = "timeout_pending_verify"
    FAILED = "failed"


TIMEOUT_PROFILE_SECONDS = {
    "search_alarm": 20,
    "create_alarm": 60,
    "modify_alarm": 90,
    "delete_alarm": 60,
    "generic_device_action": 60,
}


@dataclass(frozen=True)
class TimeoutVerificationResult:
    tool_name: str
    state: str
    device_status: str
    should_retry: bool
    should_create_fallback: bool
    reason: str
    verified_payload: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def get_timeout_seconds(tool_name: str) -> int:
    return TIMEOUT_PROFILE_SECONDS.get(tool_name, TIMEOUT_PROFILE_SECONDS["generic_device_action"])


def verify_alarm_modify_timeout(
    desired: Dict[str, Any],
    search_after_timeout: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]],
) -> TimeoutVerificationResult:
    """Verify modify_alarm timeout with a second search before retrying.

    desired may contain alarmTime, alarmTitle, and entityId.  search_after_timeout
    must perform a narrow query, preferably rangeType=next or a time window.
    """
    after = search_after_timeout(desired) or {}
    desired_time = str(desired.get("alarmTime", ""))
    desired_title = str(desired.get("alarmTitle", ""))
    after_time = str(after.get("alarmTime", ""))
    after_title = str(after.get("alarmTitle", ""))

    time_matches = bool(desired_time and desired_time == after_time)
    title_matches = not desired_title or desired_title == after_title

    if time_matches and title_matches:
        return TimeoutVerificationResult(
            tool_name="modify_alarm",
            state=DeviceActionState.SUCCESS_WITH_TIMEOUT_RECEIPT.value,
            device_status=DeviceActionState.CONNECTED_BUT_ACTION_TIMEOUT.value,
            should_retry=False,
            should_create_fallback=False,
            reason="modify_alarm timed out, but second search verified the desired alarm state",
            verified_payload=after,
        )

    return TimeoutVerificationResult(
        tool_name="modify_alarm",
        state=DeviceActionState.TIMEOUT_PENDING_VERIFY.value,
        device_status=DeviceActionState.CONNECTED_BUT_ACTION_TIMEOUT.value,
        should_retry=False,
        should_create_fallback=True,
        reason="modify_alarm timed out and second search did not verify the desired state; fallback may be used after duplicate check",
        verified_payload=after or None,
    )


def normalize_search_alarm_arguments(arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Never default to rangeType=all for linked workflows."""
    args = dict(arguments or {})
    if args.get("rangeType") == "all" or not args:
        args["rangeType"] = "next"
    return args
