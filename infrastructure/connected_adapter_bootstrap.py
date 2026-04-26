"""Connected Adapter Bootstrap - 小艺连接端 adapter 自举与安全探测。

V9.2 目标：
- session_connected=true 且 call_device_tool 可见时，先自举 adapter，再跑 L0/L1 安全路由。
- adapter_loaded=false 时，不直接执行 query_note/query_alarm/query_contact/get_location。
- 自动进入 reload/rebind/minimal/direct/service-specific 恢复链。
- probe_only 不产生副作用。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Any, Callable


class AdapterStatus(str, Enum):
    LOADED = "loaded"
    PARTIAL = "partial"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


class AdapterRecoveryStep(str, Enum):
    RELOAD_ADAPTER = "reload_adapter"
    REBIND_CALL_DEVICE_TOOL = "rebind_call_device_tool"
    PROBE_MINIMAL_SERVICE = "probe_minimal_service"
    SWITCH_TO_DIRECT_TOOL_BRIDGE = "switch_to_direct_tool_bridge"
    SERVICE_SPECIFIC_PROBE = "service_specific_probe"
    HUMAN_ACTION_REQUIRED = "human_action_required"


@dataclass
class ConnectedAdapterConfig:
    runtime_mode: str = "probe_only"
    probe_only: bool = True
    max_route_seconds: float = 15.0
    max_total_seconds: float = 60.0
    allow_side_effects: bool = False
    safe_routes: tuple[str, ...] = (
        "route.query_note",
        "route.query_alarm",
        "route.query_contact",
        "route.get_location",
        "route.query_message_status",
        "route.list_recent_messages",
    )


@dataclass
class AdapterProbeResult:
    name: str
    status: str
    detail: str = ""
    latency_ms: float | None = None


@dataclass
class ConnectedAdapterState:
    session_connected: bool = True
    runtime_bridge_ready: bool = False
    call_device_tool_available: bool = False
    adapter_loaded: bool = False
    adapter_status: AdapterStatus = AdapterStatus.UNAVAILABLE
    connected_runtime: str = "partial"
    recovery_steps: list[str] = field(default_factory=list)
    probes: list[AdapterProbeResult] = field(default_factory=list)
    failure_type: str | None = None
    human_action_required: bool = False
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    finished_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_connected": self.session_connected,
            "runtime_bridge_ready": self.runtime_bridge_ready,
            "call_device_tool_available": self.call_device_tool_available,
            "adapter_loaded": self.adapter_loaded,
            "adapter_status": self.adapter_status.value,
            "connected_runtime": self.connected_runtime,
            "recovery_steps": list(self.recovery_steps),
            "probes": [p.__dict__ for p in self.probes],
            "failure_type": self.failure_type,
            "human_action_required": self.human_action_required,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


class ConnectedAdapterBootstrap:
    """Adapter 自举器。

    `device_tool_probe` 是可选依赖注入函数，真实连接端可传入 call_device_tool 探测器；
    CI/sandbox 下不传也能 deterministic dry-run。
    """

    def __init__(
        self,
        config: ConnectedAdapterConfig | None = None,
        device_tool_probe: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None,
    ) -> None:
        self.config = config or ConnectedAdapterConfig()
        self.device_tool_probe = device_tool_probe

    def detect_runtime_bridge(self) -> bool:
        if self.device_tool_probe is not None:
            return True
        # sandbox/dry-run 默认认为小艺会话存在，但真实 adapter 未加载，只能 partial。
        return False

    def bootstrap(self) -> ConnectedAdapterState:
        state = ConnectedAdapterState(session_connected=True)
        state.runtime_bridge_ready = self.detect_runtime_bridge()
        state.call_device_tool_available = state.runtime_bridge_ready

        if state.runtime_bridge_ready:
            minimal = self.probe_minimal_service()
            state.probes.append(minimal)
            if minimal.status == "ok":
                state.adapter_loaded = True
                state.adapter_status = AdapterStatus.LOADED
                state.connected_runtime = "ready"
            else:
                self._recover_adapter(state)
        else:
            state.failure_type = "adapter_not_loaded"
            self._recover_adapter(state)

        state.finished_at = datetime.utcnow().isoformat() + "Z"
        return state

    def _recover_adapter(self, state: ConnectedAdapterState) -> None:
        for step in (
            AdapterRecoveryStep.RELOAD_ADAPTER,
            AdapterRecoveryStep.REBIND_CALL_DEVICE_TOOL,
            AdapterRecoveryStep.PROBE_MINIMAL_SERVICE,
            AdapterRecoveryStep.SWITCH_TO_DIRECT_TOOL_BRIDGE,
            AdapterRecoveryStep.SERVICE_SPECIFIC_PROBE,
        ):
            state.recovery_steps.append(step.value)
            probe = self._execute_recovery_step(step)
            state.probes.append(probe)
            if probe.status == "ok":
                state.adapter_loaded = True
                state.adapter_status = AdapterStatus.PARTIAL
                state.connected_runtime = "partial"
                state.failure_type = None
                return

        state.recovery_steps.append(AdapterRecoveryStep.HUMAN_ACTION_REQUIRED.value)
        state.adapter_loaded = False
        state.adapter_status = AdapterStatus.FAILED
        state.connected_runtime = "partial"
        state.failure_type = state.failure_type or "adapter_not_loaded"
        state.human_action_required = True

    def _execute_recovery_step(self, step: AdapterRecoveryStep) -> AdapterProbeResult:
        if self.device_tool_probe is None:
            # deterministic: no real tool bridge, no side effects; recovery stays partial/failed.
            return AdapterProbeResult(name=step.value, status="skipped", detail="no_real_device_tool_in_sandbox")

        try:
            result = self.device_tool_probe(step.value, {"probe_only": self.config.probe_only})
            ok = bool(result.get("ok") or result.get("status") in {"ok", "success", "ready"})
            return AdapterProbeResult(name=step.value, status="ok" if ok else "failed", detail=str(result)[:500])
        except Exception as exc:
            return AdapterProbeResult(name=step.value, status="failed", detail=str(exc))

    def probe_minimal_service(self) -> AdapterProbeResult:
        if self.device_tool_probe is None:
            return AdapterProbeResult(name="minimal_service", status="skipped", detail="no_real_device_tool_in_sandbox")

        try:
            result = self.device_tool_probe("minimal_service", {"probe_only": True})
            ok = bool(result.get("ok") or result.get("status") in {"ok", "success", "ready"})
            return AdapterProbeResult(name="minimal_service", status="ok" if ok else "failed", detail=str(result)[:500])
        except Exception as exc:
            return AdapterProbeResult(name="minimal_service", status="failed", detail=str(exc))

    def should_execute_route(self, route_id: str, state: ConnectedAdapterState) -> tuple[bool, str]:
        if route_id not in self.config.safe_routes:
            return False, "route_not_in_l0_l1_safe_allowlist"
        if not self.config.probe_only and not self.config.allow_side_effects:
            return False, "side_effects_disabled"
        if not state.adapter_loaded:
            return False, "adapter_not_loaded_recovery_required"
        return True, "allowed_probe"

    def smoke_route(self, route_id: str, state: ConnectedAdapterState) -> dict[str, Any]:
        allowed, reason = self.should_execute_route(route_id, state)
        if not allowed:
            return {
                "route_id": route_id,
                "status": "skipped",
                "reason": reason,
                "probe_only": self.config.probe_only,
                "side_effect": False,
            }

        if self.device_tool_probe is None:
            return {
                "route_id": route_id,
                "status": "dry_run_ok",
                "reason": "sandbox_probe_only",
                "probe_only": self.config.probe_only,
                "side_effect": False,
            }

        try:
            result = self.device_tool_probe(route_id, {"probe_only": self.config.probe_only})
            return {
                "route_id": route_id,
                "status": "ok" if result.get("status") in {"ok", "success", "ready"} or result.get("ok") else "failed",
                "result": result,
                "probe_only": self.config.probe_only,
                "side_effect": False,
            }
        except Exception as exc:
            return {
                "route_id": route_id,
                "status": "timeout_or_error",
                "error": str(exc),
                "probe_only": self.config.probe_only,
                "side_effect": False,
            }


def build_default_bootstrap(probe_only: bool = True) -> ConnectedAdapterBootstrap:
    return ConnectedAdapterBootstrap(ConnectedAdapterConfig(probe_only=probe_only, runtime_mode="probe_only" if probe_only else "connected_runtime"))
