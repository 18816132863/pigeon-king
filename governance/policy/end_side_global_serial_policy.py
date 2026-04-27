"""V24.7 policy declaration: all end-side actions are single-lane serial."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

END_SIDE_ACTION_KINDS = frozenset({'alarm','notification','calendar','gui_action','file','app_action','settings','device_tool'})

@dataclass(frozen=True)
class EndSideSerialPolicyDecision:
    must_serialize: bool
    reason: str

def classify_end_side_action(action_kind: str) -> EndSideSerialPolicyDecision:
    normalized = (action_kind or '').strip().lower()
    if normalized in END_SIDE_ACTION_KINDS:
        return EndSideSerialPolicyDecision(True, 'end_side_action_requires_global_serial_lane')
    return EndSideSerialPolicyDecision(False, 'non_end_side_action_may_run_outside_device_lane')

def assert_all_end_side_actions_serialized(action_kinds: Iterable[str], *, used_global_serial_executor: bool) -> None:
    needs_serial = any(classify_end_side_action(kind).must_serialize for kind in action_kinds)
    if needs_serial and not used_global_serial_executor:
        raise AssertionError('end-side actions must use EndSideGlobalSerialExecutor')
