from __future__ import annotations

from .schemas import (
    ActionSpec,
    ActionStatus,
    AdapterStatus,
    ToolAdapterSpec,
    GuardedExecutionResult,
    new_id,
)


class SideEffectExecutor:
    """V151: guarded executor.

    This executor is safe by default: high-risk actions never execute directly.
    It returns dry-run or waiting-approval results.
    """

    def execute(self, action: ActionSpec, adapter: ToolAdapterSpec, approved: bool = False) -> GuardedExecutionResult:
        if adapter.status != AdapterStatus.ACTIVE:
            return GuardedExecutionResult(
                id=new_id("exec"),
                action_id=action.id,
                status=ActionStatus.FAILED,
                dry_run=True,
                executed=False,
                reason="adapter missing or disabled",
                rollback_hint="no side effect occurred",
            )

        if action.requires_approval and not approved:
            return GuardedExecutionResult(
                id=new_id("exec"),
                action_id=action.id,
                status=ActionStatus.WAITING_APPROVAL,
                dry_run=True,
                executed=False,
                reason="approval required before external or irreversible side effect",
                rollback_hint="resume from checkpoint after approval",
                output={"dry_run": True, "adapter": adapter.name},
            )

        # Even when approved, dangerous payment/delete/install is represented as a controlled dry-run unless a real executor is injected later.
        if action.kind.value in {"pay", "delete", "install", "device_control", "send"}:
            return GuardedExecutionResult(
                id=new_id("exec"),
                action_id=action.id,
                status=ActionStatus.DRY_RUN,
                dry_run=True,
                executed=False,
                reason="side-effect action prepared but not executed by safe default executor",
                rollback_hint="no external side effect occurred",
                output={"prepared_action": action.kind.value, "target": action.target},
            )

        return GuardedExecutionResult(
            id=new_id("exec"),
            action_id=action.id,
            status=ActionStatus.EXECUTED,
            dry_run=False,
            executed=True,
            reason="safe local/reversible action executed in controlled mode",
            rollback_hint="re-run previous artifact snapshot if needed",
            output={"adapter": adapter.name, "target": action.target},
        )
