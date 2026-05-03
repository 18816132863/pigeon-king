"""Capability Executor - 设备能力执行器"""

from typing import Any, Dict, Optional


class CapabilityExecutor:
    """设备能力执行器
    
    负责执行虚拟设备能力调用
    """
    
    def __init__(self):
        self._capabilities = {}
    
    def register(self, capability_name: str, handler: callable) -> None:
        """注册能力"""
        self._capabilities[capability_name] = handler
    
    def execute(
        self,
        capability: str,
        params: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """执行能力
        
        Args:
            capability: 能力名称
            params: 执行参数
            context: 执行上下文
            
        Returns:
            执行结果
        """
        params = params or {}
        context = context or {}
        
        if capability not in self._capabilities:
            return {
                "status": "error",
                "error": f"能力未注册: {capability}",
                "capability": capability
            }
        
        handler = self._capabilities[capability]
        try:
            result = handler(params, context)
            return {
                "status": "success",
                "result": result,
                "capability": capability
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "capability": capability
            }
    
    def is_registered(self, capability: str) -> bool:
        """检查能力是否已注册"""
        return capability in self._capabilities


# 全局执行器实例
_executor = None


def get_executor() -> CapabilityExecutor:
    """获取全局执行器实例"""
    global _executor
    if _executor is None:
        _executor = CapabilityExecutor()
    return _executor
