"""
V11.0 Connected Adapter Bootstrap

给 scripts/check_connected_adapter.py 和运行入口使用的统一启动探测层。
它不再把“未接通端侧工具”当成失败，而是返回可被策略层消费的状态。
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from platform_adapter.connection_state import probe_device_connection


@dataclass
class ConnectedAdapterState:
    session_connected: bool
    runtime_bridge_ready: bool
    call_device_tool_available: bool
    adapter_loaded: bool
    adapter_status: str
    connected_runtime: str
    failure_type: Optional[str]
    human_action_required: bool
    recovery_steps: List[str]
    strategy: Dict[str, Any]
    raw_probe: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ConnectedAdapterBootstrap:
    def __init__(self, *, probe_only: bool = True, assume_session_connected: bool = True):
        self.probe_only = probe_only
        self.assume_session_connected = assume_session_connected

    def bootstrap(self) -> ConnectedAdapterState:
        state = probe_device_connection(assume_session_connected=self.assume_session_connected)

        if state.adapter_status == "connected":
            strategy = {
                "default_mode": "direct_or_confirm_then_direct",
                "side_effect_mode": "confirm_then_direct",
                "query_mode": "direct",
                "auto_adjusted": True,
            }
        elif state.adapter_status == "probe_only":
            strategy = {
                "default_mode": "local_fallback",
                "side_effect_mode": "confirm_then_queue",
                "query_mode": "local_fallback",
                "auto_adjusted": True,
            }
        else:
            strategy = {
                "default_mode": "skill_default",
                "side_effect_mode": "confirm_then_queue",
                "query_mode": "local_fallback",
                "auto_adjusted": True,
            }

        return ConnectedAdapterState(
            session_connected=state.session_connected,
            runtime_bridge_ready=state.runtime_bridge_ready,
            call_device_tool_available=state.call_device_tool_available,
            adapter_loaded=state.adapter_loaded,
            adapter_status=state.adapter_status,
            connected_runtime=state.connected_runtime,
            failure_type=state.failure_type,
            human_action_required=state.human_action_required,
            recovery_steps=state.recovery_steps,
            strategy=strategy,
            raw_probe=state.to_dict(),
        )


def build_default_bootstrap(*, probe_only: bool = True) -> ConnectedAdapterBootstrap:
    return ConnectedAdapterBootstrap(probe_only=probe_only, assume_session_connected=True)
