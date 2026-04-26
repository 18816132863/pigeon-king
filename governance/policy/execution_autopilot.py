"""V11.4 Execution Autopilot: strategy + confirmation + circuit + queue."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Optional
from governance.policy.adaptive_execution_policy import select_execution_strategy
from governance.security.strong_confirmation import require_strong_confirmation
from platform_adapter.capability_registry import get_capability, register_default_capabilities
from platform_adapter.runtime_state_store import enqueue_action, register_action, transition_action
from platform_adapter.timeout_circuit import CircuitBreaker
@dataclass
class AutopilotDecision:
    status: str; mode: str; action_id: str; idempotency_key: str; requires_confirmation: bool; queued: bool; direct_allowed: bool; reason: str; next_action: str; strategy: Dict[str, Any]; capability: Dict[str, Any]; confirmation: Dict[str, Any]; circuit: Dict[str, Any]
    def to_dict(self) -> Dict[str, Any]: return asdict(self)
def plan_runtime_action(*,capability,op_name,payload=None,task_id=None,risk_level="L1",provided_confirmation_token=None,result_uncertain=False,timeout=False,failure_type=None,db_path=None):
    register_default_capabilities(db_path=db_path); payload=payload or {}; action=register_action(capability=capability,op_name=op_name,payload=payload,task_id=task_id,risk_level=risk_level,db_path=db_path); cap=get_capability(capability,db_path=db_path); breaker=CircuitBreaker(f"{capability}:{op_name}",db_path=db_path); circuit_state=breaker.get_state()
    strategy=select_execution_strategy(capability=capability,op_name=op_name,risk_level=risk_level,adapter_status=cap.status,failure_type=failure_type,result_uncertain=result_uncertain,timeout=timeout)
    confirmation=require_strong_confirmation(action=op_name,payload=payload,provided_token=provided_confirmation_token,risk_level=risk_level if strategy.confirmation_required else "L1",result_uncertain=result_uncertain or timeout).to_dict()
    if not breaker.allow_request() and strategy.mode in {"direct","confirm_then_direct"}:
        q=enqueue_action(action.action_id,delivery_mode="circuit_open",db_path=db_path); transition_action(action.action_id,"queued",reason="circuit_open",result={"queue_id":q},db_path=db_path)
        return AutopilotDecision("queued","queued_for_delivery",action.action_id,action.idempotency_key,False,True,False,"熔断器打开，避免连续卡死，已转队列/降级","等待冷却后重新探测，或人工确认后单次执行",strategy.to_dict(),cap.to_dict(),confirmation,circuit_state.to_dict()).to_dict()
    if strategy.mode=="hold_for_result_check":
        transition_action(action.action_id,"hold_for_result_check",reason=strategy.reason,db_path=db_path)
        return AutopilotDecision("hold_for_result_check",strategy.mode,action.action_id,action.idempotency_key,True,False,False,strategy.reason,strategy.next_action,strategy.to_dict(),cap.to_dict(),confirmation,circuit_state.to_dict()).to_dict()
    if strategy.confirmation_required and not confirmation.get("allowed"):
        transition_action(action.action_id,"requires_confirmation",reason=confirmation.get("reason",strategy.reason),result={"confirmation":confirmation},db_path=db_path)
        return AutopilotDecision("requires_confirmation",strategy.mode,action.action_id,action.idempotency_key,True,False,False,confirmation.get("reason",strategy.reason),"把 confirmation_token 带回后再执行，或选择取消该动作",strategy.to_dict(),cap.to_dict(),confirmation,circuit_state.to_dict()).to_dict()
    if strategy.mode in {"confirm_then_queue","local_fallback"}:
        q=enqueue_action(action.action_id,delivery_mode=strategy.mode,db_path=db_path); transition_action(action.action_id,"queued",reason=strategy.reason,result={"queue_id":q},db_path=db_path)
        return AutopilotDecision("queued",strategy.mode,action.action_id,action.idempotency_key,False,True,False,strategy.reason,strategy.next_action,strategy.to_dict(),cap.to_dict(),confirmation,circuit_state.to_dict()).to_dict()
    transition_action(action.action_id,"planned",reason="direct_allowed",db_path=db_path)
    return AutopilotDecision("allowed",strategy.mode,action.action_id,action.idempotency_key,False,False,True,strategy.reason,strategy.next_action,strategy.to_dict(),cap.to_dict(),confirmation,circuit_state.to_dict()).to_dict()
