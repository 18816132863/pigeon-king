"""
Runtime Probe - V11.0

统一运行时探测：
- connected：可直接调用端侧工具
- probe_only：会话/环境存在，但 runtime bridge 未接好，策略自动降级
- offline：本地默认模式
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from .connection_state import probe_device_connection


class RuntimeProbe:
    """运行时探测器"""

    @staticmethod
    def detect_environment() -> Dict[str, Any]:
        conn = probe_device_connection(assume_session_connected=True)
        env = {
            "is_xiaoyi": conn.connected_runtime == "xiaoyi",
            "is_harmonyos": os.environ.get("HARMONYOS_VERSION") is not None or os.environ.get("OHOS_VERSION") is not None,
            "is_web": os.environ.get("WEB_ENV") is not None or os.environ.get("HTTP_HOST") is not None,
            "is_cli": False,
            "has_local_sqlite": Path("data/tasks.db").exists(),
            "has_external_database": os.environ.get("DATABASE_URL") is not None,
            "has_redis": os.environ.get("REDIS_URL") is not None or os.environ.get("REDIS_HOST") is not None,
            "has_docker": Path("/.dockerenv").exists() or os.environ.get("KUBERNETES_SERVICE_HOST") is not None,
            "device_connection": conn.to_dict(),
        }
        env["has_database"] = env["has_local_sqlite"] or env["has_external_database"]
        env["runtime_mode"] = RuntimeProbe._determine_mode(env)
        return env

    @staticmethod
    def _determine_mode(env: Dict[str, Any]) -> str:
        state = env.get("device_connection", {}).get("adapter_status")
        if state == "connected":
            return "platform_enhanced"
        if env["has_external_database"] and env["has_redis"]:
            return "self_hosted_enhanced"
        if state == "probe_only":
            return "platform_probe_fallback"
        return "skill_default"

    @staticmethod
    def get_recommended_adapter() -> str:
        conn = probe_device_connection(assume_session_connected=True)
        if conn.adapter_status in {"connected", "probe_only"}:
            return "xiaoyi"
        return "null"

    @staticmethod
    def probe_adapter(adapter_name: str) -> Dict[str, Any]:
        return RuntimeProbe.probe_adapter_sync(adapter_name)

    @staticmethod
    def probe_adapter_sync(adapter_name: str) -> Dict[str, Any]:
        if adapter_name == "null":
            return {"adapter": "null", "available": False, "capabilities": {}}
        if adapter_name == "xiaoyi":
            conn = probe_device_connection(assume_session_connected=True)
            queue_available = conn.can_queue_or_fallback
            return {
                "adapter": "xiaoyi",
                "available": queue_available,
                "direct_available": conn.can_direct_invoke,
                "state": conn.adapter_status,
                "environment_exists": conn.session_connected,
                "capabilities": {
                    "task_scheduling": queue_available,
                    "message_sending": queue_available,
                    "notification": queue_available,
                },
                "connection": conn.to_dict(),
            }
        return {"adapter": adapter_name, "available": False, "error": f"Unknown adapter: {adapter_name}"}


# 便捷函数

def detect_runtime() -> Dict[str, Any]:
    return RuntimeProbe.detect_environment()


def get_runtime_mode() -> str:
    return RuntimeProbe.detect_environment()["runtime_mode"]
