"""
Xiaoyi Adapter - V75.2 Reality Closure Fix

V75.2 修复：
- 所有端侧调用必须经过 DeviceSerialLane 串行化
- DeviceAction 参数统一为 action_id, action_kind, payload, idempotency_key
- calendar / notification 不允许绕过串行队列
- 如果没有 serial lane，返回配置错误，不能悄悄直连
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .base import PlatformAdapter, PlatformCapability, PlatformCapabilityState
from .connection_state import probe_device_connection, DeviceConnectionState
from .invoke_guard import guarded_platform_call, create_fallback_result, InvokeResult, generate_idempotency_key
from .invocation_ledger import record_invocation
from .result_normalizer import NormalizedStatus
from governance.policy.adaptive_execution_policy import select_execution_strategy

# V75.2: 导入端侧串行化器
try:
    from orchestration.end_side_serial_lanes_v3 import EndSideSerialLaneV3, DeviceAction
    _serial_lane = EndSideSerialLaneV3()
except ImportError:
    _serial_lane = None
    DeviceAction = None


class SerialLaneNotAvailableError(Exception):
    """串行化器不可用错误"""
    pass


class XiaoyiAdapter(PlatformAdapter):
    name = "xiaoyi"
    description = "Xiaoyi/HarmonyOS platform adapter with V11 stable execution policy"

    SIDE_EFFECTING_CAPABILITIES = {
        PlatformCapability.MESSAGE_SENDING,
        PlatformCapability.TASK_SCHEDULING,
        PlatformCapability.NOTIFICATION,
    }

    def __init__(self):
        self._capabilities: Dict[PlatformCapability, PlatformCapabilityState] = {}
        self._initialized = False
        self._connection: Optional[DeviceConnectionState] = None
        self._environment_exists = False
        self._call_device_tool_available = False
        self._device_connected = False

    def _check_call_device_tool_available(self) -> bool:
        return bool(probe_device_connection().call_device_tool_available)

    def _ensure_initialized_sync(self):
        if self._initialized:
            return

        self._connection = probe_device_connection(assume_session_connected=True)
        self._environment_exists = self._connection.session_connected
        self._call_device_tool_available = self._connection.call_device_tool_available
        self._device_connected = self._connection.adapter_status == "connected"

        direct_available = self._connection.can_direct_invoke
        queue_available = self._connection.can_queue_or_fallback

        self._capabilities = {
            PlatformCapability.TASK_SCHEDULING: PlatformCapabilityState(
                capability=PlatformCapability.TASK_SCHEDULING,
                available=queue_available,
                description="Task scheduling via Xiaoyi when connected; queued/fallback when probe_only",
                limitations=[] if direct_available else ["direct_runtime_bridge_not_ready", "queued_or_fallback_only"],
            ),
            PlatformCapability.MESSAGE_SENDING: PlatformCapabilityState(
                capability=PlatformCapability.MESSAGE_SENDING,
                available=queue_available,
                description="Message sending via Xiaoyi when connected; queued/fallback when probe_only",
                limitations=[] if direct_available else ["direct_runtime_bridge_not_ready", "requires_confirm_before_queue"],
            ),
            PlatformCapability.NOTIFICATION: PlatformCapabilityState(
                capability=PlatformCapability.NOTIFICATION,
                available=queue_available,
                description="Notification push via platform or local queued fallback",
                limitations=[] if direct_available else ["direct_runtime_bridge_not_ready", "local_fallback"],
            ),
        }
        self._initialized = True

    async def _ensure_initialized(self):
        self._ensure_initialized_sync()

    async def probe(self) -> Dict[str, Any]:
        await self._ensure_initialized()
        assert self._connection is not None

        available_caps = {cap.value: status.available for cap, status in self._capabilities.items()}
        direct_caps = {cap.value: self._connection.can_direct_invoke for cap in self._capabilities}

        return {
            "adapter": self.name,
            "available": self._connection.can_queue_or_fallback,
            "state": self._connection.adapter_status,
            "device_connected": self._device_connected,
            "call_device_tool_available": self._call_device_tool_available,
            "capabilities": available_caps,
            "direct_capabilities": direct_caps,
            "failure_type": self._connection.failure_type,
            "auto_adjusted_strategy": True,
            "message": "Xiaoyi adapter connected" if self._device_connected else "Xiaoyi adapter probe_only/offline; strategy auto-adjusted to fallback/queue",
            "connection": self._connection.to_dict(),
        }

    async def get_capability(self, capability: PlatformCapability) -> Optional[PlatformCapabilityState]:
        await self._ensure_initialized()
        return self._capabilities.get(capability)

    async def invoke(self, capability: PlatformCapability, params: Dict[str, Any]) -> Dict[str, Any]:
        await self._ensure_initialized()
        assert self._connection is not None

        status = self._capabilities.get(capability)
        if not status:
            return {
                "success": False,
                "status": "failed",
                "error": f"Unknown capability: {capability.value}",
                "error_code": "UNKNOWN_CAPABILITY",
                "user_message": f"未知能力: {capability.value}",
            }

        if capability == PlatformCapability.MESSAGE_SENDING:
            return await self._invoke_message_sending_guarded(params)
        if capability == PlatformCapability.TASK_SCHEDULING:
            return await self._invoke_task_scheduling_guarded(params)
        if capability == PlatformCapability.NOTIFICATION:
            return await self._invoke_notification_guarded(params)

        return {
            "success": False,
            "status": "failed",
            "error": f"Capability {capability.value} not implemented",
            "error_code": "NOT_IMPLEMENTED",
            "user_message": f"该能力尚未实现: {capability.value}",
        }

    def _strategy_for(self, capability: str, op_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        assert self._connection is not None
        return select_execution_strategy(
            capability=capability,
            op_name=op_name,
            risk_level=params.get("risk_level", "L3"),
            adapter_status=self._connection.adapter_status,
            failure_type=self._connection.failure_type,
        ).to_dict()

    async def _fallback_or_queue(self, capability: str, op_name: str, params: Dict[str, Any], idempotency_key: str, reason: str) -> Dict[str, Any]:
        result = create_fallback_result(
            capability=capability,
            op_name=op_name,
            idempotency_key=idempotency_key,
            reason=reason,
        )
        self._record(capability, op_name, params, result, idempotency_key)
        data = self._result_to_dict(result)
        data["strategy"] = self._strategy_for(capability, op_name, params)
        return data

    async def _invoke_message_sending_guarded(self, params: Dict[str, Any]) -> Dict[str, Any]:
        idempotency_key = generate_idempotency_key(
            task_id=params.get("task_id"),
            capability="MESSAGE_SENDING",
            payload={"phone": params.get("phone_number"), "msg": params.get("message")},
        )

        if not self._call_device_tool_available:
            return await self._fallback_or_queue(
                "MESSAGE_SENDING", "send_message", params, idempotency_key,
                "runtime bridge/call_device_tool not available; queued instead of hard failure",
            )

        # V75.2: 必须通过 DeviceSerialLane，不允许直连
        if _serial_lane is None or DeviceAction is None:
            return {
                "success": False,
                "status": "failed",
                "error": "DeviceSerialLane not available - configuration error",
                "error_code": "SERIAL_LANE_NOT_AVAILABLE",
                "user_message": "系统配置错误：端侧串行化器不可用",
                "idempotency_key": idempotency_key,
            }

        async def _call():
            # V75.2: 使用正确的 DeviceAction 参数
            action = DeviceAction(
                action_id=f"msg_{idempotency_key[:8]}",
                action_kind="send_message",
                payload={"phoneNumber": params.get("phone_number"), "content": params.get("message")},
                idempotency_key=idempotency_key,
            )
            
            # 同步执行器包装
            def sync_executor(a: DeviceAction) -> Dict[str, Any]:
                import asyncio
                try:
                    from tools import call_device_tool
                    loop = asyncio.new_event_loop()
                    try:
                        result = loop.run_until_complete(
                            call_device_tool(toolName="send_message", arguments=a.payload)
                        )
                        return result
                    finally:
                        loop.close()
                except ImportError:
                    return {"status": "error", "error": "call_device_tool not importable"}
            
            receipt = _serial_lane.submit_many([action], sync_executor)[0]
            
            if receipt.status in ("success", "success_with_timeout_receipt"):
                return {"status": "success", "receipt": receipt.to_dict()}
            elif receipt.status == "timeout_pending_verify":
                return {"status": "action_timeout", "receipt": receipt.to_dict(), "needs_verify": True}
            else:
                return {"status": "failed", "receipt": receipt.to_dict()}

        result = await guarded_platform_call(
            capability="MESSAGE_SENDING",
            op_name="send_message",
            call_coro=_call,
            timeout_seconds=int(params.get("timeout_seconds", 30)),
            idempotency_key=idempotency_key,
            side_effecting=True,
            task_id=params.get("task_id"),
            payload=params,
        )
        self._record("MESSAGE_SENDING", "send_message", params, result, idempotency_key)
        data = self._result_to_dict(result)
        data["strategy"] = self._strategy_for("MESSAGE_SENDING", "send_message", params)
        return data

    async def _invoke_task_scheduling_guarded(self, params: Dict[str, Any]) -> Dict[str, Any]:
        idempotency_key = generate_idempotency_key(
            task_id=params.get("task_id"),
            capability="TASK_SCHEDULING",
            payload={"title": params.get("title"), "start": params.get("start_time")},
        )

        if not self._call_device_tool_available:
            return await self._fallback_or_queue(
                "TASK_SCHEDULING", "create_calendar_event", params, idempotency_key,
                "runtime bridge/call_device_tool not available; calendar event queued/fallback",
            )

        # V75.2: 必须通过 DeviceSerialLane，不允许直连
        if _serial_lane is None or DeviceAction is None:
            return {
                "success": False,
                "status": "failed",
                "error": "DeviceSerialLane not available - configuration error",
                "error_code": "SERIAL_LANE_NOT_AVAILABLE",
                "user_message": "系统配置错误：端侧串行化器不可用",
                "idempotency_key": idempotency_key,
            }

        async def _call():
            # V75.2: 使用正确的 DeviceAction 参数
            action = DeviceAction(
                action_id=f"cal_{idempotency_key[:8]}",
                action_kind="create_calendar_event",
                payload={
                    "title": params.get("title"),
                    "dtStart": params.get("start_time"),
                    "dtEnd": params.get("end_time")
                },
                idempotency_key=idempotency_key,
            )
            
            # 同步执行器包装
            def sync_executor(a: DeviceAction) -> Dict[str, Any]:
                import asyncio
                try:
                    from tools import call_device_tool
                    loop = asyncio.new_event_loop()
                    try:
                        result = loop.run_until_complete(
                            call_device_tool(toolName="create_calendar_event", arguments=a.payload)
                        )
                        return result
                    finally:
                        loop.close()
                except ImportError:
                    return {"status": "error", "error": "call_device_tool not importable"}
            
            receipt = _serial_lane.submit_many([action], sync_executor)[0]
            
            if receipt.status in ("success", "success_with_timeout_receipt"):
                return {"status": "success", "receipt": receipt.to_dict()}
            elif receipt.status == "timeout_pending_verify":
                return {"status": "action_timeout", "receipt": receipt.to_dict(), "needs_verify": True}
            else:
                return {"status": "failed", "receipt": receipt.to_dict()}

        result = await guarded_platform_call(
            capability="TASK_SCHEDULING",
            op_name="create_calendar_event",
            call_coro=_call,
            timeout_seconds=int(params.get("timeout_seconds", 30)),
            idempotency_key=idempotency_key,
            side_effecting=True,
            task_id=params.get("task_id"),
            payload=params,
        )
        self._record("TASK_SCHEDULING", "create_calendar_event", params, result, idempotency_key)
        data = self._result_to_dict(result)
        data["strategy"] = self._strategy_for("TASK_SCHEDULING", "create_calendar_event", params)
        return data

    async def _invoke_notification_guarded(self, params: Dict[str, Any]) -> Dict[str, Any]:
        idempotency_key = generate_idempotency_key(
            task_id=params.get("task_id"),
            capability="NOTIFICATION",
            payload={"title": params.get("title")},
        )

        if not self._call_device_tool_available:
            return await self._fallback_or_queue(
                "NOTIFICATION", "create_notification", params, idempotency_key,
                "runtime bridge/call_device_tool not available; notification queued/fallback",
            )

        # V75.2: 必须通过 DeviceSerialLane，不允许直连
        if _serial_lane is None or DeviceAction is None:
            return {
                "success": False,
                "status": "failed",
                "error": "DeviceSerialLane not available - configuration error",
                "error_code": "SERIAL_LANE_NOT_AVAILABLE",
                "user_message": "系统配置错误：端侧串行化器不可用",
                "idempotency_key": idempotency_key,
            }

        async def _call():
            # V75.2: 使用正确的 DeviceAction 参数
            action = DeviceAction(
                action_id=f"notif_{idempotency_key[:8]}",
                action_kind="create_notification",
                payload={
                    "title": params.get("title"),
                    "content": params.get("content"),
                    "notificationId": params.get("notification_id")
                },
                idempotency_key=idempotency_key,
            )
            
            # 同步执行器包装
            def sync_executor(a: DeviceAction) -> Dict[str, Any]:
                import asyncio
                try:
                    from tools import call_device_tool
                    loop = asyncio.new_event_loop()
                    try:
                        result = loop.run_until_complete(
                            call_device_tool(toolName="create_notification", arguments=a.payload)
                        )
                        return result
                    finally:
                        loop.close()
                except ImportError:
                    return {"status": "error", "error": "call_device_tool not importable"}
            
            receipt = _serial_lane.submit_many([action], sync_executor)[0]
            
            if receipt.status in ("success", "success_with_timeout_receipt"):
                return {"status": "success", "receipt": receipt.to_dict()}
            elif receipt.status == "timeout_pending_verify":
                return {"status": "action_timeout", "receipt": receipt.to_dict(), "needs_verify": True}
            else:
                return {"status": "failed", "receipt": receipt.to_dict()}

        result = await guarded_platform_call(
            capability="NOTIFICATION",
            op_name="create_notification",
            call_coro=_call,
            timeout_seconds=int(params.get("timeout_seconds", 30)),
            idempotency_key=idempotency_key,
            side_effecting=True,
            task_id=params.get("task_id"),
            payload=params,
        )
        self._record("NOTIFICATION", "create_notification", params, result, idempotency_key)
        data = self._result_to_dict(result)
        data["strategy"] = self._strategy_for("NOTIFICATION", "create_notification", params)
        return data

    def _record(self, capability: str, platform_op: str, params: Dict[str, Any], result: InvokeResult, idempotency_key: str) -> None:
        try:
            record_invocation(
                capability=capability,
                platform_op=platform_op,
                normalized_status=result.normalized_status,
                task_id=params.get("task_id"),
                idempotency_key=idempotency_key,
                side_effecting=True,
                request_json=params,
                raw_result_json=result.raw_result,
                error_code=result.error_code,
                user_message=result.user_message,
                result_uncertain=result.result_uncertain,
                fallback_used=result.fallback_used,
                elapsed_ms=result.elapsed_ms,
            )
        except Exception:
            # 审计不可用不能反向阻塞主流程；主流程仍返回可读结果。
            pass

    def _result_to_dict(self, result: InvokeResult) -> Dict[str, Any]:
        return {
            "success": result.normalized_status == NormalizedStatus.COMPLETED,
            "status": result.normalized_status,
            "capability": result.capability,
            "error": result.error_code,
            "error_code": result.error_code,
            "user_message": result.user_message,
            "raw_result": result.raw_result,
            "should_retry": result.should_retry,
            "result_uncertain": result.result_uncertain,
            "side_effecting": result.side_effecting,
            "fallback_used": result.fallback_used,
            "idempotency_key": result.idempotency_key,
            "elapsed_ms": result.elapsed_ms,
        }

    async def is_available(self) -> bool:
        await self._ensure_initialized()
        return bool(self._connection and self._connection.can_queue_or_fallback)
