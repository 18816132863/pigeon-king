"""
V11.0 Adaptive Execution Policy

把“失败后人工处理”改成“执行前自动选策略”：
- connected: 直连执行
- probe_only/offline + 副作用: 队列/fallback，必要时强确认
- timeout/uncertain: 不自动重复副作用，要求确认结果后再执行
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


SIDE_EFFECT_CAPABILITIES = {
    "MESSAGE_SENDING",
    "TASK_SCHEDULING",
    "NOTIFICATION",
    "phone",
    "alarm",
    "calendar",
    "file_write",
    "delete",
    "send_message",
    "create_calendar_event",
}

HIGH_RISK_LEVELS = {"L3", "L4", "high", "critical"}


@dataclass
class ExecutionStrategy:
    mode: str
    confirmation_required: bool
    confirmation_level: str
    allow_auto_retry: bool
    allow_fallback: bool
    reason: str
    next_action: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _is_side_effecting(capability: str, op_name: str = "") -> bool:
    cap = str(capability or "")
    op = str(op_name or "")
    return cap in SIDE_EFFECT_CAPABILITIES or op in SIDE_EFFECT_CAPABILITIES or any(x in op.lower() for x in ["send", "delete", "create", "update", "call"])


def select_execution_strategy(
    *,
    capability: str,
    op_name: str = "",
    risk_level: str = "L1",
    adapter_status: str = "probe_only",
    failure_type: Optional[str] = None,
    result_uncertain: bool = False,
    timeout: bool = False,
) -> ExecutionStrategy:
    side_effecting = _is_side_effecting(capability, op_name)
    high_risk = str(risk_level) in HIGH_RISK_LEVELS

    if result_uncertain or timeout:
        return ExecutionStrategy(
            mode="hold_for_result_check",
            confirmation_required=True,
            confirmation_level="strong_confirm" if side_effecting else "normal_confirm",
            allow_auto_retry=False,
            allow_fallback=False,
            reason="上次结果不确定/超时，为避免重复执行，禁止静默重试",
            next_action="先查验执行结果；确认未执行后再重新发起",
        )

    if adapter_status == "connected":
        if high_risk or side_effecting:
            return ExecutionStrategy(
                mode="confirm_then_direct",
                confirmation_required=True,
                confirmation_level="strong_confirm" if high_risk else "confirm_once",
                allow_auto_retry=False,
                allow_fallback=True,
                reason="设备端已连接，但动作有副作用或风险较高",
                next_action="强确认/确认一次后直连执行；失败时转队列/fallback",
            )
        return ExecutionStrategy(
            mode="direct",
            confirmation_required=False,
            confirmation_level="none",
            allow_auto_retry=True,
            allow_fallback=True,
            reason="设备端已连接且为低风险查询动作",
            next_action="直接执行，失败可自动重试或降级",
        )

    if adapter_status in {"probe_only", "offline"}:
        if side_effecting or high_risk:
            return ExecutionStrategy(
                mode="confirm_then_queue",
                confirmation_required=True,
                confirmation_level="strong_confirm" if high_risk else "confirm_once",
                allow_auto_retry=False,
                allow_fallback=True,
                reason=f"设备端不可直连({failure_type or adapter_status})，副作用动作不能静默失败或静默重试",
                next_action="确认后转 queued_for_delivery/local_fallback，并在下次执行前重新探测",
            )
        return ExecutionStrategy(
            mode="local_fallback",
            confirmation_required=False,
            confirmation_level="none",
            allow_auto_retry=True,
            allow_fallback=True,
            reason=f"设备端不可直连({failure_type or adapter_status})，低风险动作自动降级",
            next_action="使用本地默认能力或只读模拟结果，同时记录降级原因",
        )

    return ExecutionStrategy(
        mode="blocked",
        confirmation_required=True,
        confirmation_level="strong_confirm",
        allow_auto_retry=False,
        allow_fallback=False,
        reason="未知运行状态，进入保护模式",
        next_action="输出诊断报告，不执行副作用动作",
    )
