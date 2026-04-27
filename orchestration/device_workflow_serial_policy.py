"""
V23.4 serial policy for device-linked workflows.

For reminder workflows with alarm + hiboard push + chat cron, the safe order is:
1. alarm device action
2. hiboard / negative-one-screen push
3. openclaw cron / main-dialog push
4. final verification and report
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List

SAFE_REMINDER_ORDER = ("alarm", "hiboard_push", "chat_cron", "final_verify")


@dataclass(frozen=True)
class SerialPolicyReport:
    passed: bool
    normalized_order: List[str]
    reason: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def normalize_reminder_workflow_order(steps: Iterable[str]) -> List[str]:
    step_set = list(dict.fromkeys(steps))
    ordered = [s for s in SAFE_REMINDER_ORDER if s in step_set]
    ordered.extend([s for s in step_set if s not in ordered])
    return ordered


def validate_reminder_workflow_order(steps: Iterable[str]) -> SerialPolicyReport:
    normalized = normalize_reminder_workflow_order(steps)
    passed = normalized[: len(SAFE_REMINDER_ORDER)] == [s for s in SAFE_REMINDER_ORDER if s in normalized]
    return SerialPolicyReport(
        passed=passed,
        normalized_order=normalized,
        reason="device reminder workflows must serialize alarm before push/cron/final verification",
    )
