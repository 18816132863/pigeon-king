"""
V11.0 Device Connection State

统一判断设备端/运行时桥接/平台适配器是否真正可用。
原则：
1. 不再把“设备端默认已连接”当作真实连接；默认只能是 assumed/probe_only。
2. 只要无法直接调用端侧能力，就自动转入 queued/fallback，而不是让任务硬失败。
3. 给上层返回机器可读的 failure_type，供策略自动调整。
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import importlib.util
import os
import sys


@dataclass
class DeviceConnectionState:
    session_connected: bool
    runtime_bridge_ready: bool
    call_device_tool_available: bool
    adapter_loaded: bool
    adapter_status: str
    connected_runtime: str
    failure_type: Optional[str]
    human_action_required: bool
    recovery_steps: List[str]
    details: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def can_direct_invoke(self) -> bool:
        return self.adapter_status == "connected" and self.call_device_tool_available

    @property
    def can_queue_or_fallback(self) -> bool:
        return self.adapter_loaded or self.runtime_bridge_ready or self.session_connected


def _truthy_env(name: str) -> bool:
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "y", "on", "connected"}


def _module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:
        return False


def probe_device_connection(*, assume_session_connected: bool = True) -> DeviceConnectionState:
    """探测设备连接状态。

    assume_session_connected=True 表示会话层默认认为“可能连接”，但不会把它升级成
    可直接调用。真正可直接调用必须同时满足 runtime bridge / call_device_tool 可用。
    """
    env_xiaoyi = os.environ.get("XIAOYI_ENV") is not None
    env_harmony = os.environ.get("HARMONYOS_VERSION") is not None or os.environ.get("OHOS_VERSION") is not None
    env_openclaw = _truthy_env("OPENCLAW_RUNTIME")
    env_forced_connected = _truthy_env("XIAOYI_DEVICE_CONNECTED")
    xiaoyi_module_loaded = "xiaoyi" in sys.modules

    tools_module_available = _module_available("tools")
    runtime_bridge_ready = env_openclaw or env_forced_connected or tools_module_available
    session_connected = bool(assume_session_connected or env_xiaoyi or env_harmony or env_openclaw or env_forced_connected or xiaoyi_module_loaded)
    call_device_tool_available = bool(runtime_bridge_ready)
    adapter_loaded = bool(session_connected or runtime_bridge_ready)

    if call_device_tool_available:
        adapter_status = "connected"
        failure_type = None
        human_action_required = False
        recovery_steps: List[str] = []
    elif session_connected:
        adapter_status = "probe_only"
        failure_type = "RUNTIME_BRIDGE_NOT_READY"
        human_action_required = False
        recovery_steps = [
            "自动转入 queued_for_delivery 或本地 fallback",
            "下一次任务执行前重新探测 call_device_tool/runtime bridge",
            "高风险副作用动作保持强确认，不做静默重试",
        ]
    else:
        adapter_status = "offline"
        failure_type = "DEVICE_SESSION_NOT_CONNECTED"
        human_action_required = False
        recovery_steps = [
            "自动降级为 skill_default/local_fallback",
            "需要真实端侧能力时再提示连接或授权",
        ]

    connected_runtime = "xiaoyi" if (env_xiaoyi or env_harmony or env_openclaw or env_forced_connected) else "local"

    return DeviceConnectionState(
        session_connected=session_connected,
        runtime_bridge_ready=runtime_bridge_ready,
        call_device_tool_available=call_device_tool_available,
        adapter_loaded=adapter_loaded,
        adapter_status=adapter_status,
        connected_runtime=connected_runtime,
        failure_type=failure_type,
        human_action_required=human_action_required,
        recovery_steps=recovery_steps,
        details={
            "env_xiaoyi": env_xiaoyi,
            "env_harmony": env_harmony,
            "env_openclaw": env_openclaw,
            "env_forced_connected": env_forced_connected,
            "xiaoyi_module_loaded": xiaoyi_module_loaded,
            "tools_module_available": tools_module_available,
        },
    )
