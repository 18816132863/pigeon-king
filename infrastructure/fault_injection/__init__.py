#!/usr/bin/env python3
"""
故障注入模块 — 从 V96 门脚本提炼

提供标准故障注入框架：模拟导入失败、JSON 损坏、状态哈希漂移、审计回退等。
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable


class FaultInjector:
    """故障注入器"""

    FAULT_TYPES = [
        "import_failure",
        "json_corruption",
        "memory_rejection",
        "search_no_results",
        "self_improvement_fail",
        "commit_blocked",
    ]

    def __init__(self, name: str = "fault_test"):
        self.name = name
        self.faults: List[Dict[str, Any]] = []

    def inject(self, fault_type: str, handler: Callable) -> Dict[str, Any]:
        """注入指定类型的故障并运行处理"""
        if fault_type not in self.FAULT_TYPES:
            return {"fault_type": fault_type, "status": "unknown", "error": f"Unknown fault type: {fault_type}"}
        
        result = {
            "fault_type": fault_type,
            "status": "unknown",
            "recovery_action": "",
            "error": None,
        }

        try:
            handler()
            result["status"] = "pass"
            result["recovery_action"] = self._default_recovery(fault_type)
        except Exception as e:
            result["status"] = "fail"
            result["error"] = str(e)[:200]

        # 验证——故障注入后不应有真实环境副作用
        self._assert_no_real_effects()
        self.faults.append(result)
        return result

    def _default_recovery(self, fault_type: str) -> str:
        """每种故障类型的默认恢复动作"""
        recoveries = {
            "import_failure": "fallback to stub module",
            "json_corruption": "regenerate from state",
            "memory_rejection": "MWG + OBS fallback write",
            "search_no_results": "return empty + warning",
            "self_improvement_fail": "dry-run only, skip commit",
            "commit_blocked": "block + log to gateway",
        }
        return recoveries.get(fault_type, "unknown")

    def _assert_no_real_effects(self):
        """断言无真实环境副作用"""
        assert os.environ.get("NO_EXTERNAL_API") == "true", "泄漏了外部 API 调用"
        assert os.environ.get("NO_REAL_PAYMENT") == "true", "泄漏了真实支付"

    def summary(self) -> Dict[str, Any]:
        """返回测试摘要"""
        passed = [f for f in self.faults if f["status"] == "pass"]
        failed = [f for f in self.faults if f["status"] == "fail"]
        return {
            "name": self.name,
            "total": len(self.faults),
            "passed": len(passed),
            "failed": len(failed),
            "details": self.faults,
        }
