from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from .schemas import (
    ActionBridgeResult,
    BridgeStatus,
    ActionStatus,
    EvidenceKind,
    NotificationLevel,
    HandoffStatus,
    BackgroundRunStatus,
    new_id,
)
from .action_dsl import ActionDSLCompiler
from .device_session import DeviceSessionManager
from .tool_adapter_registry import ToolAdapterRegistry
from .evidence_capture import EvidenceCapture
from .side_effect_executor import SideEffectExecutor
from .notification_center import NotificationCenter
from .handoff_inbox import HandoffInbox
from .background_run_ledger import BackgroundRunLedger
from .real_world_scenario_harness import RealWorldScenarioHarness


class ActionBridgeKernel:
    """V156: orchestrates bounded real-world action preparation."""

    def __init__(self, root: str | Path = ".action_bridge_state"):
        self.root = Path(root)
        self.dsl = ActionDSLCompiler()
        self.devices = DeviceSessionManager(self.root)
        self.adapters = ToolAdapterRegistry(self.root)
        self.evidence = EvidenceCapture(self.root)
        self.executor = SideEffectExecutor()
        self.notifications = NotificationCenter(self.root)
        self.handoffs = HandoffInbox(self.root)
        self.bg = BackgroundRunLedger(self.root)
        self.scenarios = RealWorldScenarioHarness()

    def run_cycle(self, goal: str, approved: bool = False) -> ActionBridgeResult:
        run_id = new_id("bridge")
        action = self.dsl.compile(goal)
        adapter = self.adapters.select(action.kind)
        device = self.devices.best_for("dry_run")
        self.evidence.record(run_id, EvidenceKind.INPUT, "goal", {"goal": goal})
        self.evidence.record(run_id, EvidenceKind.DECISION, "compiled_action", {
            "action_id": action.id,
            "kind": action.kind.value,
            "risk": action.risk.value,
            "requires_approval": action.requires_approval,
        })

        execution = self.executor.execute(action, adapter, approved=approved)
        self.evidence.record(run_id, EvidenceKind.DRY_RUN if execution.dry_run else EvidenceKind.OUTPUT, "execution_result", {
            "status": execution.status.value,
            "reason": execution.reason,
            "output": execution.output,
        })

        handoff = None
        if execution.status == ActionStatus.WAITING_APPROVAL:
            handoff = self.handoffs.create(
                title=f"Approval required: {action.kind.value}",
                reason=execution.reason,
                action_id=action.id,
            )
            notification = self.notifications.notify(
                NotificationLevel.ACTION_REQUIRED,
                "需要审批",
                f"{goal} 需要人工确认后才能继续。",
                action_required=True,
            )
        elif execution.status == ActionStatus.BLOCKED:
            notification = self.notifications.notify(NotificationLevel.CRITICAL, "动作被阻断", execution.reason, action_required=False)
        elif execution.status == ActionStatus.FAILED:
            notification = self.notifications.notify(NotificationLevel.WARNING, "动作失败", execution.reason, action_required=False)
        else:
            notification = self.notifications.notify(NotificationLevel.INFO, "动作已准备", execution.reason, action_required=False)

        bg = self.bg.create(
            title=f"action_bridge:{action.kind.value}",
            checkpoint={"id": run_id, "action_id": action.id, "status": execution.status.value},
            waiting=execution.status == ActionStatus.WAITING_APPROVAL,
        )

        scenario = self.scenarios.evaluate({
            "action_compiled": bool(action.id),
            "adapter_selected": adapter.status.value == "active",
            "evidence_recorded": len(self.evidence.list_run(run_id)) >= 3,
            "notification_created": bool(notification.id),
            "high_risk": action.requires_approval,
            "handoff_created": handoff is not None,
            "no_unapproved_side_effect": not (action.requires_approval and execution.executed and not approved),
            "background_checkpoint": bool(bg.id),
        })

        if action.requires_approval and not approved:
            bridge_status = BridgeStatus.WAITING_APPROVAL
            next_action = "等待用户审批，审批后从 checkpoint 恢复"
        elif execution.status == ActionStatus.FAILED:
            bridge_status = BridgeStatus.BLOCKED
            next_action = "修复 adapter 或改成安全动作"
        elif execution.dry_run:
            bridge_status = BridgeStatus.DRY_RUN_READY
            next_action = "已完成安全预演，可由受控真实执行器接管"
        else:
            bridge_status = BridgeStatus.READY
            next_action = "动作桥准备完成，可进入下一层执行链"

        return ActionBridgeResult(
            run_id=run_id,
            goal=goal,
            bridge_status=bridge_status,
            action_kind=action.kind,
            action_risk=action.risk,
            device_status=device.status,
            adapter_status=adapter.status,
            execution_status=execution.status,
            notification_level=notification.level,
            handoff_status=handoff.status if handoff else None,
            background_status=bg.status,
            scenario_score=scenario.score,
            evidence_count=len(self.evidence.list_run(run_id)),
            next_action=next_action,
            details={
                "action_id": action.id,
                "adapter": adapter.name,
                "device": device.device_name,
                "execution_reason": execution.reason,
                "rollback_hint": execution.rollback_hint,
                "scenario_failures": scenario.failures,
                "handoff_id": handoff.id if handoff else None,
                "background_run_id": bg.id,
            },
        )


_DEFAULT: Optional[ActionBridgeKernel] = None


def init_action_bridge(root: str | Path = ".action_bridge_state") -> Dict:
    global _DEFAULT
    _DEFAULT = ActionBridgeKernel(root)
    return {"status": "ok", "root": str(Path(root)), "modules": 10}


def run_action_bridge_cycle(goal: str, approved: bool = False, root: str | Path = ".action_bridge_state") -> ActionBridgeResult:
    global _DEFAULT
    if _DEFAULT is None or _DEFAULT.root != Path(root):
        _DEFAULT = ActionBridgeKernel(root)
    return _DEFAULT.run_cycle(goal, approved=approved)
