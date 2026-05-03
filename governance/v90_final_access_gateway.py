"""
V90 FinalAccessGateway — 统一能力访问网关。

所有能力调用都必须经过此网关，绝不允许直接调用底层模块。
在离线模式下，自动路由到本地 mock / dry-run / 文件后备。

架构位置: L5 Governance — 六层架构的唯一安全出口。
依赖: infrastructure.offline_mode, infrastructure.offline_adapters
"""
from __future__ import annotations
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional, Callable

try:
    from infrastructure.offline_mode import (
        OFFLINE_MODE, NO_EXTERNAL_API, NO_REAL_SEND,
        audit_info, audit_warning, audit_error,
        mock_or_fallback, MockResult,
        get_memory_redis, get_file_redis, get_sqlite_repo,
        get_in_process_queue, get_mock_celery,
        get_mock_connector_factory, get_alert_drafts,
        get_mock_tts, get_mock_auto_git, get_mock_auto_backup,
        STATE_DIR,
    )
    from infrastructure.offline_adapters import get_adapter as get_offline_adapter
    OFFLINE_OK = True
except ImportError as e:
    OFFLINE_OK = False
    STATE_DIR = Path(os.environ.get("WORKSPACE", "/home/sandbox/.openclaw/workspace")) / ".offline_state"
    OFFLINE_MODE = True
    NO_EXTERNAL_API = True
    NO_REAL_SEND = True
    @dataclass
    class MockResult:
        success: bool = True
        data: Dict = field(default_factory=dict)
        warning: str = "offline"
        source: str = "offline"
    def _noop(*a, **kw): pass
    audit_info = _noop; audit_warning = _noop; audit_error = _noop
    def mock_or_fallback(*a, **kw): return MockResult()
    def get_memory_redis(): return None
    def get_file_redis(): return None
    def get_sqlite_repo(): return None
    def get_in_process_queue(): return None
    def get_mock_celery(): return None
    def get_mock_connector_factory(): return None
    def get_alert_drafts(): return None
    def get_mock_tts(): return None
    def get_mock_auto_git(): return None
    def get_mock_auto_backup(): return None
    def get_offline_adapter(n): return None


# ── 路由策略 ────────────────────────────────────────────
CAPABILITY_ROUTES: Dict[str, str] = {
    # L1 Core
    "identity.check": "core.digital_twin.identity_drift_guard",
    "self_evolution.run_cycle": "core.self_evolution_ops.self_improvement_loop",
    "self_evolution.propose_improvement": "core.self_evolution_ops.self_improvement_loop",
    # L2 Memory Context
    "memory.knowledge_graph": "memory_context.personal_knowledge_graph_v5",
    "memory.preference_evolution": "memory_context.preference_evolution_model_v7",
    "memory.writeback_guard": "memory_context.memory_writeback_guard_v2",
    # L3 Orchestration
    "orchestration.solution_search": "infrastructure.solution_search_orchestrator",
    "orchestration.capability_extension": "infrastructure.capability_self_extension",
    # L4 Execution
    "execution.multimodal_search": "offline_adapter.multimodal",
    "execution.cross_lingual_search": "offline_adapter.cross_lingual",
    "execution.visual_agent": "offline_adapter.visual_agent",
    "execution.tts": "offline_infra.tts",
    "execution.auto_git": "offline_infra.auto_git",
    "execution.auto_backup": "offline_infra.auto_backup",
    "execution.device_serial": "execution.device_serial_lane_v6",
    # L5 Governance
    "governance.sandbox_gate": "offline_adapter.sandbox_gate",
    "governance.regression_matrix": "offline_adapter.regression_matrix",
    "governance.alert": "offline_infra.alert",
    "governance.audit": "offline_infra.audit",
    # L6 Infrastructure
    "infrastructure.celery_task": "offline_infra.celery",
    "infrastructure.connector": "offline_infra.connector",
    "infrastructure.fusion_engine": "offline_adapter.fusion_engines",
    "infrastructure.learning_evaluator": "offline_adapter.learning_evaluator",
    "infrastructure.speculative_decode": "offline_adapter.speculative_decoder",
}


@dataclass
class GatewayAccessLog:
    ts: float = field(default_factory=time.time)
    capability: str = ""
    route: str = ""
    mode: str = "offline"  # offline / online / fallback
    result_summary: str = ""
    latency_ms: float = 0


class V90FinalAccessGateway:
    """V90 FinalAccessGateway — 统一能力访问网关。

    规则：
    1. 所有能力都必须经过 call()，不允许直接调用底层模块
    2. 离线模式自动路由到 mock / dry-run / 本地文件
    3. 每次调用记录审计日志
    """

    def __init__(self, log_path: Path = None):
        self._log_path = log_path or STATE_DIR / "v90_gateway_access.jsonl"
        self._access_log: list[GatewayAccessLog] = []
        self._call_count = 0
        self._route_error_count = 0
        audit_info("V90FinalAccessGateway", "initialized", offline_mode=OFFLINE_MODE)

    # ── 对外唯一入口 ────────────────────────────────────
    def call(self, capability: str, params: dict = None, force_online: bool = False) -> dict:
        """统一入口。所有能力调用必须经过此方法。"""
        start = time.time()
        params = params or {}
        self._call_count += 1

        # 确定路由
        route = CAPABILITY_ROUTES.get(capability, "unknown")
        mode = "online" if force_online and not OFFLINE_MODE else "offline" if OFFLINE_MODE else "online"

        result: dict = {"gateway_version": "V90", "capability": capability, "route": route, "mode": mode}

        try:
            if capability == "identity.check":
                result.update(self._handle_identity_check(params))
            elif capability.startswith("self_evolution."):
                result.update(self._handle_self_evolution(capability, params))
            elif capability.startswith("memory."):
                result.update(self._handle_memory(capability, params))
            elif capability.startswith("execution."):
                result.update(self._handle_execution(capability, params, mode))
            elif capability.startswith("orchestration."):
                result.update(self._handle_orchestration(capability, params, mode))
            elif capability.startswith("governance."):
                result.update(self._handle_governance(capability, params, mode))
            elif capability.startswith("infrastructure."):
                result.update(self._handle_infrastructure(capability, params, mode))
            else:
                result["status"] = "route_not_found"
                result["error"] = f"unknown_capability: {capability}"
                self._route_error_count += 1
                audit_warning("V90FinalAccessGateway", "route_not_found", capability=capability)
        except Exception as e:
            result["status"] = "gateway_error"
            result["error"] = str(e)
            audit_error("V90FinalAccessGateway", "gateway_exception", capability=capability, error=str(e))
            self._route_error_count += 1

        latency = (time.time() - start) * 1000
        log_entry = GatewayAccessLog(capability=capability, route=route, mode=mode, result_summary=result.get("status", "unknown"), latency_ms=latency)
        self._access_log.append(log_entry)
        self._write_access_log(log_entry)

        result["gateway_latency_ms"] = round(latency, 2)
        result["call_no"] = self._call_count
        return result

    def _write_access_log(self, entry: GatewayAccessLog):
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._log_path, "a") as f:
            f.write(json.dumps({
                "ts": entry.ts, "capability": entry.capability,
                "route": entry.route, "mode": entry.mode,
                "result": entry.result_summary, "latency_ms": entry.latency_ms,
            }, ensure_ascii=False) + "\n")

    # ── 各层处理 ────────────────────────────────────────
    def _handle_identity_check(self, params: dict) -> dict:
        if OFFLINE_OK:
            from infrastructure.offline_adapters import enhanced_identity_drift_check
            return enhanced_identity_drift_check(params.get("twin", {}))
        return {"status": "safe", "must_not_impersonate_user": True, "offline": True}

    def _handle_self_evolution(self, capability: str, params: dict) -> dict:
        # V91 修复: 直接返回 dict，不使用 mock_or_fallback（避免 MockResult 对象导致 dict.update TypeError）
        return {"status": "dry_run_ok", "capability": capability, "offline": True}

    def _handle_memory(self, capability: str, params: dict) -> dict:
        # V91 修复: 直接返回 dict
        return {"status": "offline_memory_ok", "capability": capability, "offline": True}

    def _handle_execution(self, capability: str, params: dict, mode: str) -> dict:
        if capability == "execution.tts":
            tts = get_mock_tts()
            if tts:
                r = tts.synthesize(params.get("text", ""), params.get("voice", "default"))
                return {"status": "mock_tts_done", **r}
        elif capability == "execution.auto_git":
            git = get_mock_auto_git()
            if git:
                action = params.get("action", "status")
                fn = getattr(git, action, git.status)
                return {"status": "mock_git_done", **fn()}
        elif capability == "execution.auto_backup":
            backup = get_mock_auto_backup()
            if backup:
                return {"status": "mock_backup_done", **backup.backup(params.get("name"))}
        elif capability == "execution.multimodal_search" and OFFLINE_OK:
            adapter = get_offline_adapter("multimodal")
            if adapter:
                r = adapter.search_image(params.get("query", ""), params.get("limit", 5))
                return {"status": "offline_multimodal_done", "data": r.data}
        elif capability == "execution.cross_lingual_search" and OFFLINE_OK:
            adapter = get_offline_adapter("cross_lingual")
            if adapter:
                r = adapter.search(params.get("query", ""), params.get("source", "zh"), params.get("target", "en"))
                return {"status": "offline_cross_lingual_done", "data": r.data}
        elif capability == "execution.visual_agent" and OFFLINE_OK:
            adapter = get_offline_adapter("visual_agent")
            if adapter:
                r = adapter.plan_action(params.get("screenshot", ""), params.get("goal", ""))
                return {"status": "offline_visual_agent_done", "data": r.data}
        return {"status": "offline_execution_ok", "capability": capability, "offline": True}

    def _handle_orchestration(self, capability: str, params: dict, mode: str) -> dict:
        # V91 修复: solution_search 走离线本地搜索
        if capability == "orchestration.solution_search":
            if OFFLINE_OK:
                adapter = get_offline_adapter("solution_search")
                if adapter is not None:
                    result = adapter.search(params.get("query", ""), params.get("limit", 10))
                    # result 已包含完整的 status/mode/route/action_semantic/side_effects/requires_api
                    return result
            # 回退：直接通过 orchestrator
            try:
                from infrastructure.solution_search_orchestrator import SolutionSearchOrchestrator
                orch = SolutionSearchOrchestrator()
                return orch.search(params.get("query", ""), params.get("limit", 10))
            except ImportError:
                return {
                    "status": "ok", "mode": "offline",
                    "route": "orchestration.solution_search",
                    "action_semantic": "analyze",
                    "side_effects": False, "requires_api": False,
                    "result": [],
                    "warning": "no_local_solution_found",
                }
        return {"status": "offline_orchestration_ok", "capability": capability, "offline": True}

    def _handle_governance(self, capability: str, params: dict, mode: str) -> dict:
        if capability == "governance.alert":
            alerts = get_alert_drafts()
            if alerts:
                alert_id = alerts.create(params.get("title", "offline alert"), params.get("body", ""), params.get("channel", "system"))
                return {"status": "alert_drafted", "alert_id": alert_id, "sent": False}
        elif capability == "governance.sandbox_gate" and OFFLINE_OK:
            adapter = get_offline_adapter("sandbox_gate")
            if adapter:
                return {"status": "sandbox_evaluated", **adapter.evaluate(params)}
        elif capability == "governance.regression_matrix" and OFFLINE_OK:
            adapter = get_offline_adapter("regression_matrix")
            if adapter:
                return {"status": "regression_evaluated", **adapter.evaluate(params)}
        return {"status": "offline_governance_ok", "capability": capability, "offline": True}

    def _handle_infrastructure(self, capability: str, params: dict, mode: str) -> dict:
        if capability == "infrastructure.celery_task":
            celery = get_mock_celery()
            if celery:
                task_id = celery.send_task(params.get("name", "offline_task"), params.get("args", ()), params.get("kwargs", {}))
                return {"status": "task_enqueued", "task_id": task_id}
        elif capability == "infrastructure.connector":
            factory = get_mock_connector_factory()
            if factory:
                c = factory.create(params.get("type", "generic"), params.get("config", {}))
                return {"status": "connector_created", "connector": c.data}
        elif capability == "infrastructure.fusion_engine" and OFFLINE_OK:
            adapter = get_offline_adapter("fusion_engines")
            if adapter:
                return {"status": "fusion_scan_done", **adapter.scan()}
        elif capability == "infrastructure.learning_evaluator" and OFFLINE_OK:
            adapter = get_offline_adapter("learning_evaluator")
            if adapter:
                return {"status": "learning_evaluated", **adapter.evaluate(params.get("feedback", []))}
        elif capability == "infrastructure.speculative_decode" and OFFLINE_OK:
            adapter = get_offline_adapter("speculative_decoder")
            if adapter:
                r = adapter.decode(params.get("prompt", ""), params.get("tokens", 50))
                return {"status": "speculative_decode_done", **r}
        return {"status": "offline_infra_ok", "capability": capability, "offline": True}

    # ── 诊断 ────────────────────────────────────────────
    def get_status(self) -> dict:
        return {
            "version": "V90",
            "offline_mode": OFFLINE_MODE,
            "no_external_api": NO_EXTERNAL_API,
            "no_real_send": NO_REAL_SEND,
            "total_calls": self._call_count,
            "route_errors": self._route_error_count,
            "routes_configured": len(CAPABILITY_ROUTES),
            "recent_calls": [
                {"capability": e.capability, "mode": e.mode, "result": e.result_summary}
                for e in self._access_log[-20:]
            ],
        }

    def list_routes(self) -> list:
        return [{"capability": k, "route": v} for k, v in CAPABILITY_ROUTES.items()]


# ── 单例 ────────────────────────────────────────────────
_DEFAULT_GATEWAY: Optional[V90FinalAccessGateway] = None


def get_v90_gateway() -> V90FinalAccessGateway:
    global _DEFAULT_GATEWAY
    if _DEFAULT_GATEWAY is None:
        _DEFAULT_GATEWAY = V90FinalAccessGateway()
    return _DEFAULT_GATEWAY


# 便捷函数：所有能力调用的唯一入口
def gateway_call(capability: str, params: dict = None, force_online: bool = False) -> dict:
    return get_v90_gateway().call(capability, params, force_online)


__all__ = [
    "V90FinalAccessGateway", "get_v90_gateway", "gateway_call",
    "CAPABILITY_ROUTES",
]


# v92_solution_search_offline_patch
def v92_handle_solution_search_offline(query: str = "", **kwargs):
    try:
        from infrastructure.solution_search_orchestrator import offline_solution_search
        return offline_solution_search(query=query, limit=int(kwargs.get("limit", 20)))
    except Exception as exc:
        return {"status":"ok", "route":"orchestration.solution_search", "mode":"offline", "action_semantic":"analyze", "side_effects":False, "requires_api":False, "result":[], "warning":"solution_search_offline_fallback", "error":str(exc)}
