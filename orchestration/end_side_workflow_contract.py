"""
V24.1 End-side Workflow Contract.

Layer: L3 Orchestration.

Compiles reminder requests into a fixed serial workflow.  This intentionally
does not directly call the device.  It gives execution a safe order.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


ARCHITECTURE_LAYER = "L3 Orchestration"


@dataclass(frozen=True)
class WorkflowPhase:
    name: str
    order: int
    layer: str
    action: str
    must_be_serial: bool = True
    requires_verification: bool = False


@dataclass(frozen=True)
class EndSideWorkflowContract:
    workflow_type: str
    user_goal: str
    phases: list[WorkflowPhase]
    constraints: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compile_three_channel_reminder(user_goal: str) -> EndSideWorkflowContract:
    return EndSideWorkflowContract(
        workflow_type="three_channel_reminder",
        user_goal=user_goal,
        constraints={
            "device_connected_is_not_action_success": True,
            "modify_alarm_timeout_requires_second_search": True,
            "do_not_use_search_alarm_all_by_default": True,
            "no_parallel_side_effects": True,
            "overall_status_allows_partial_success": True,
        },
        phases=[
            WorkflowPhase("alarm", 1, "L4 Execution", "search_then_create_or_modify_alarm", True, True),
            WorkflowPhase("hiboard_push", 2, "L4 Execution", "push_to_hiboard", True, True),
            WorkflowPhase("chat_cron", 3, "L4 Execution", "schedule_openclaw_cron", True, True),
            WorkflowPhase("final_verify", 4, "L3 Orchestration", "summarize_and_verify_transaction", True, True),
        ],
    )


def assert_serial_order(contract: EndSideWorkflowContract) -> bool:
    orders = [phase.order for phase in contract.phases]
    return orders == sorted(orders) and all(phase.must_be_serial for phase in contract.phases)
