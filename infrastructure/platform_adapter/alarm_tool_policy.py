"""
V23.9 Alarm Tool Policy.

Layer: L4 Execution / Platform Adapter.

Rules encoded here:
- search_alarm defaults to rangeType=next, not all.
- modify/delete require entityId.
- modify_alarm has a longer timeout profile.
- timeout must be verified, not treated as offline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ARCHITECTURE_LAYER = "L4 Execution / Platform Adapter"


DEFAULT_TIMEOUTS_SECONDS = {
    "search_alarm": 20,
    "create_alarm": 60,
    "modify_alarm": 90,
    "delete_alarm": 60,
}


@dataclass(frozen=True)
class AlarmToolCall:
    tool_name: str
    arguments: dict[str, Any]
    timeout_seconds: int
    requires_verify_after_timeout: bool


def normalize_search_alarm_args(arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    args = dict(arguments or {})
    # Forbid broad all-range query by default because it is known to timeout.
    if args.get("rangeType") in {None, "", "all"} and not (args.get("startTime") and args.get("endTime")):
        args["rangeType"] = "next"
    return args


def build_alarm_tool_call(tool_name: str, arguments: dict[str, Any] | None = None) -> AlarmToolCall:
    args = dict(arguments or {})
    if tool_name == "search_alarm":
        args = normalize_search_alarm_args(args)
    if tool_name in {"modify_alarm", "delete_alarm"} and not args.get("entityId"):
        raise ValueError(f"{tool_name} requires entityId from search_alarm")
    return AlarmToolCall(
        tool_name=tool_name,
        arguments=args,
        timeout_seconds=DEFAULT_TIMEOUTS_SECONDS.get(tool_name, 60),
        requires_verify_after_timeout=tool_name in {"modify_alarm", "create_alarm", "delete_alarm"},
    )


def should_retry_modify_alarm_without_verify() -> bool:
    """Hard policy: never blindly retry alarm modify after timeout."""
    return False
