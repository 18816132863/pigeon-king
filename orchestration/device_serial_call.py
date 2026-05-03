"""
V75.3 统一端侧调用入口

所有端侧动作必须通过此模块进入串行化器。
业务能力层不允许直接调用 call_device_tool。

使用方式：
    from orchestration.device_serial_call import serial_call_device_tool
    
    result = await serial_call_device_tool("alarm", "create", {"time": "0800"})
"""

from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass
import hashlib
import json
import asyncio

# 导入串行化器
try:
    from orchestration.end_side_serial_lanes_v3 import EndSideSerialLaneV3, DeviceAction
    _global_serial_lane = EndSideSerialLaneV3()
except ImportError:
    _global_serial_lane = None
    DeviceAction = None


class SerialCallError(Exception):
    """串行调用错误"""
    pass


class SerialLaneNotAvailableError(SerialCallError):
    """串行化器不可用错误"""
    pass


@dataclass
class SerialCallResult:
    """串行调用结果"""
    success: bool
    status: str
    data: Any = None
    error: str = ""
    elapsed_ms: int = 0
    idempotency_key: str = ""


def _make_idempotency_key(tool_type: str, action: str, params: Dict[str, Any]) -> str:
    """生成幂等键"""
    body = json.dumps({
        "tool": tool_type,
        "action": action,
        "params": params
    }, sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()[:16]


async def serial_call_device_tool(
    tool_type: str,
    action: str,
    params: Dict[str, Any],
    *,
    timeout_seconds: int = 30,
    idempotency_key: Optional[str] = None,
    _internal_call: bool = False
) -> SerialCallResult:
    """
    统一端侧调用入口
    
    所有端侧动作必须通过此函数进入串行化器。
    
    Args:
        tool_type: 工具类型 (alarm/calendar/file/contact/photo/note/notification)
        action: 操作类型 (search/create/modify/delete)
        params: 操作参数
        timeout_seconds: 超时时间（秒）
        idempotency_key: 幂等键（可选，自动生成）
        _internal_call: 内部调用标志（仅供串行化器回调使用）
    
    Returns:
        SerialCallResult: 调用结果
    
    Raises:
        SerialLaneNotAvailableError: 串行化器不可用
    """
    # V75.3: 必须通过串行化器，不允许直连
    if _global_serial_lane is None or DeviceAction is None:
        raise SerialLaneNotAvailableError(
            "DeviceSerialLane not available. All device actions must go through serial lane. "
            "Check orchestration.end_side_serial_lanes_v3 import."
        )
    
    # 生成幂等键
    if idempotency_key is None:
        idempotency_key = _make_idempotency_key(tool_type, action, params)
    
    # 创建 DeviceAction
    device_action = DeviceAction(
        action_id=f"{tool_type}_{idempotency_key}",
        action_kind=f"{tool_type}_{action}",
        payload=params,
        idempotency_key=idempotency_key,
    )
    
    # 执行器：调用真实的端侧工具
    def executor(a: DeviceAction) -> Dict[str, Any]:
        try:
            # 导入底层适配器（仅在此处允许）
            from infrastructure.platform_adapter.device_tool_adapter import call_device_tool
            
            # 调用端侧工具
            result = call_device_tool(tool_type, action, a.payload)
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # 通过串行化器执行
    import time
    start = time.time()
    
    receipts = _global_serial_lane.submit_many([device_action], executor)
    
    elapsed_ms = int((time.time() - start) * 1000)
    
    if not receipts:
        return SerialCallResult(
            success=False,
            status="no_receipt",
            error="串行化器未返回结果",
            elapsed_ms=elapsed_ms,
            idempotency_key=idempotency_key
        )
    
    receipt = receipts[0]
    
    # 解析结果
    if receipt.status in ("success", "success_with_timeout_receipt"):
        return SerialCallResult(
            success=True,
            status=receipt.status,
            data=receipt.result if hasattr(receipt, 'result') else None,
            elapsed_ms=elapsed_ms,
            idempotency_key=idempotency_key
        )
    elif receipt.status == "timeout_pending_verify":
        return SerialCallResult(
            success=False,
            status="timeout_pending_verify",
            error="操作超时，需要二次验证",
            elapsed_ms=elapsed_ms,
            idempotency_key=idempotency_key
        )
    elif receipt.status == "device_offline":
        return SerialCallResult(
            success=False,
            status="device_offline",
            error="设备离线",
            elapsed_ms=elapsed_ms,
            idempotency_key=idempotency_key
        )
    else:
        return SerialCallResult(
            success=False,
            status=receipt.status,
            error=receipt.reason,
            elapsed_ms=elapsed_ms,
            idempotency_key=idempotency_key
        )


def serial_call_device_tool_sync(
    tool_type: str,
    action: str,
    params: Dict[str, Any],
    **kwargs
) -> SerialCallResult:
    """
    同步版本的统一端侧调用入口
    
    用于非异步环境调用。
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        serial_call_device_tool(tool_type, action, params, **kwargs)
    )


# 导出
__all__ = [
    "serial_call_device_tool",
    "serial_call_device_tool_sync",
    "SerialCallResult",
    "SerialCallError",
    "SerialLaneNotAvailableError",
]
