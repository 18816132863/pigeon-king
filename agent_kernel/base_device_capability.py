"""
V75.2 设备能力封装基类 - Reality Closure Fix

V75.2 修复：
- 所有端侧调用必须经过 DeviceSerialLane 串行化
- 如果没有 serial lane，返回配置错误，不能悄悄直连
- 支持两种格式返回值解析
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable
import asyncio
import threading
import hashlib
import json

# V75.2: 导入端侧串行化器
try:
    from orchestration.end_side_serial_lanes_v3 import EndSideSerialLaneV3, DeviceAction
    _global_serial_lane = EndSideSerialLaneV3()
except ImportError:
    _global_serial_lane = None
    DeviceAction = None


class OperationStatus(Enum):
    """操作状态"""
    SUCCESS = "success"
    SUCCESS_WITH_TIMEOUT_RECEIPT = "success_with_timeout_receipt"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    DEVICE_OFFLINE = "device_offline"
    CONNECTED_BUT_ACTION_TIMEOUT = "connected_but_action_timeout"
    SKIPPED = "skipped"
    SKIPPED_DUPLICATE = "skipped_duplicate"


@dataclass
class OperationResult:
    """操作结果"""
    status: OperationStatus
    message: str
    data: Any = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def is_success(self) -> bool:
        """是否成功"""
        return self.status in (
            OperationStatus.SUCCESS,
            OperationStatus.SUCCESS_WITH_TIMEOUT_RECEIPT,
            OperationStatus.SKIPPED,
            OperationStatus.SKIPPED_DUPLICATE
        )
    
    def needs_verification(self) -> bool:
        """是否需要二次验证"""
        return self.status == OperationStatus.CONNECTED_BUT_ACTION_TIMEOUT


class TimeoutProfile:
    """超时配置"""
    SEARCH = 20      # 查询操作
    CREATE = 60      # 创建操作
    MODIFY = 90      # 修改操作
    DELETE = 60      # 删除操作
    DEFAULT = 30     # 默认


class BaseDeviceCapability(ABC):
    """设备能力基类"""
    
    # 子类需要定义
    CAPABILITY_NAME: str = "base"
    
    def __init__(self, call_device_tool: Callable = None, serial_lane=None):
        """
        初始化设备能力
        
        Args:
            call_device_tool: 端侧工具调用函数（仅作为回调，不直接调用）
            serial_lane: 串行化器实例（必须提供）
        """
        self.call_device_tool = call_device_tool
        self._serial_lane = serial_lane or _global_serial_lane
        self._lock = threading.Lock()
        self._pending_verifications: Dict[str, Dict] = {}
    
    def _make_idempotency_key(self, operation: str, params: Dict[str, Any]) -> str:
        """生成幂等键"""
        body = json.dumps({"cap": self.CAPABILITY_NAME, "op": operation, "params": params}, sort_keys=True)
        return hashlib.sha256(body.encode()).hexdigest()[:16]
    
    async def _execute_with_verification(
        self,
        operation: str,
        params: Dict[str, Any],
        timeout: int = TimeoutProfile.DEFAULT,
        verify_func: Callable = None
    ) -> OperationResult:
        """
        执行操作并支持二次验证
        
        V75.2: 必须通过 DeviceSerialLane，不允许直连
        
        Args:
            operation: 操作类型 (search/create/modify/delete)
            params: 操作参数
            timeout: 超时时间（秒）
            verify_func: 二次验证函数
        """
        # V75.2: 检查串行化器是否可用
        if self._serial_lane is None or DeviceAction is None:
            return OperationResult(
                status=OperationStatus.FAILED,
                message="DeviceSerialLane not available - configuration error. All device actions must go through serial lane."
            )
        
        if self.call_device_tool is None:
            return OperationResult(
                status=OperationStatus.DEVICE_OFFLINE,
                message="call_device_tool 未初始化"
            )
        
        # 生成幂等键
        idempotency_key = self._make_idempotency_key(operation, params)
        
        try:
            # V75.2: 创建 DeviceAction（使用正确的参数）
            action = DeviceAction(
                action_id=f"{self.CAPABILITY_NAME}_{idempotency_key}",
                action_kind=f"{self.CAPABILITY_NAME}_{operation}",
                payload=params,
                idempotency_key=idempotency_key,
            )
            
            # 同步执行器包装
            def sync_executor(a: DeviceAction) -> Dict[str, Any]:
                try:
                    # 调用端侧工具
                    result = self.call_device_tool(self.CAPABILITY_NAME, operation, a.payload)
                    return result
                except Exception as e:
                    return {"success": False, "error": str(e)}
            
            # 通过串行化器执行
            receipts = self._serial_lane.submit_many([action], sync_executor)
            
            if not receipts:
                return OperationResult(
                    status=OperationStatus.FAILED,
                    message="串行化器未返回结果"
                )
            
            receipt = receipts[0]
            
            # 解析结果
            if receipt.status in ("success", "success_with_timeout_receipt"):
                return OperationResult(
                    status=OperationStatus.SUCCESS if receipt.status == "success" else OperationStatus.SUCCESS_WITH_TIMEOUT_RECEIPT,
                    message="操作成功",
                    data=receipt.result if hasattr(receipt, 'result') else None
                )
            elif receipt.status == "timeout_pending_verify":
                # 超时后尝试二次验证
                if verify_func:
                    verify_result = await verify_func(params)
                    if verify_result:
                        return OperationResult(
                            status=OperationStatus.SUCCESS_WITH_TIMEOUT_RECEIPT,
                            message="超时但二次验证成功"
                        )
                return OperationResult(
                    status=OperationStatus.CONNECTED_BUT_ACTION_TIMEOUT,
                    message=f"操作超时，设备可能已执行但未收到回执"
                )
            elif receipt.status == "device_offline":
                return OperationResult(
                    status=OperationStatus.DEVICE_OFFLINE,
                    message="设备离线"
                )
            else:
                return OperationResult(
                    status=OperationStatus.FAILED,
                    message=f"操作失败: {receipt.reason}"
                )
            
        except asyncio.TimeoutError:
            return OperationResult(
                status=OperationStatus.CONNECTED_BUT_ACTION_TIMEOUT,
                message=f"操作超时（{timeout}s）"
            )
            
        except Exception as e:
            return OperationResult(
                status=OperationStatus.FAILED,
                message=str(e)
            )
    
    def _parse_result(self, result: Dict) -> OperationResult:
        """解析工具返回结果"""
        # 支持两种格式：
        # 1. {"success": True/False, ...} - 本地适配器格式
        # 2. {"code": "0000000000", ...} - 端侧工具格式
        
        # 格式1: success 字段
        if "success" in result:
            if result["success"]:
                return OperationResult(
                    status=OperationStatus.SUCCESS,
                    message=result.get("message", "操作成功"),
                    data=result
                )
            else:
                return OperationResult(
                    status=OperationStatus.FAILED,
                    message=result.get("error", result.get("message", "操作失败"))
                )
        
        # 格式2: code 字段
        code = result.get("code", "")
        
        if code == "0000000000":
            return OperationResult(
                status=OperationStatus.SUCCESS,
                message="操作成功",
                data=result.get("data")
            )
        elif code == "-303":
            return OperationResult(
                status=OperationStatus.SKIPPED,
                message="查询结果为空"
            )
        elif code == "-202":
            return OperationResult(
                status=OperationStatus.DEVICE_OFFLINE,
                message="设备离线"
            )
        else:
            return OperationResult(
                status=OperationStatus.FAILED,
                message=result.get("message", f"错误码: {code}")
            )
    
    @abstractmethod
    async def search(self, **kwargs) -> Tuple[Any, OperationResult]:
        """查询"""
        pass
    
    @abstractmethod
    async def create(self, **kwargs) -> Tuple[Any, OperationResult]:
        """创建"""
        pass
    
    @abstractmethod
    async def modify(self, **kwargs) -> OperationResult:
        """修改"""
        pass
    
    @abstractmethod
    async def delete(self, **kwargs) -> OperationResult:
        """删除"""
        pass
