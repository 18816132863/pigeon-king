#!/usr/bin/env python3
"""
通用门禁框架 V1.0 — 从 V93-V100 门脚本中提炼的核心逻辑

提供：
- 标准的门检查运行器
- JSON 报告读写
- 环境变量门控检查
- 结果聚合与验收
"""
from __future__ import annotations

import json
import os
import time
import hashlib
from pathlib import Path
from dataclasses import is_dataclass, asdict
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable


def safe_jsonable(obj: Any) -> Any:
    """递归化任何对象为 JSON 安全类型"""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Path):
        return str(obj)
    if is_dataclass(obj) and not isinstance(obj, type):
        return safe_jsonable(asdict(obj))
    if isinstance(obj, dict):
        return {str(k): safe_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [safe_jsonable(x) for x in obj]
    if hasattr(obj, "model_dump"):
        try:
            return safe_jsonable(obj.model_dump())
        except Exception:
            pass
    if hasattr(obj, "dict"):
        try:
            return safe_jsonable(obj.dict())
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        try:
            return safe_jsonable(vars(obj))
        except Exception:
            pass
    return str(obj)


def write_json(path, payload):
    """安全写入 JSON 文件"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(safe_jsonable(payload), ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path) -> Optional[dict]:
    """安全读取 JSON 文件"""
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_read_error": str(e)}


class EnvChecker:
    """环境变量门控检查"""

    REQUIRED_VARS = {
        "OFFLINE_MODE",
        "NO_EXTERNAL_API",
        "DISABLE_LLM_API",
        "DISABLE_THINKING_MODE",
        "NO_REAL_SEND",
        "NO_REAL_PAYMENT",
        "NO_REAL_DEVICE",
    }

    @staticmethod
    def check_all() -> Dict[str, bool]:
        return {v: os.environ.get(v) == "true" for v in EnvChecker.REQUIRED_VARS}

    @staticmethod
    def all_true() -> bool:
        return all(EnvChecker.check_all().values())

    @staticmethod
    def report() -> Dict[str, Any]:
        checks = EnvChecker.check_all()
        return {"env": checks, "all_ok": all(checks.values()), "violations": [k for k, v in checks.items() if not v]}


class CheckResult:
    """检查结果容器"""

    def __init__(self, name: str):
        self.name = name
        self.passed = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.details: Dict[str, Any] = {}

    def fail(self, msg: str):
        self.passed = False
        self.errors.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    def detail(self, key: str, value: Any):
        self.details[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "details": self.details,
        }


class GateRunner:
    """门禁检查运行器"""

    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.checks: List[CheckResult] = []

    def add_check(self, check: CheckResult):
        self.checks.append(check)

    def run(self, checks_fn: Callable) -> Dict[str, Any]:
        """运行一组检查函数并生成标准报告"""
        checks_fn()
        passed = [c for c in self.checks if c.passed]
        failed = [c for c in self.checks if not c.passed]
        errors = [e for c in self.checks for e in c.errors]
        warnings = [w for c in self.checks for w in c.warnings]
        return {
            "version": self.version,
            "status": "pass" if not failed else "partial",
            "check_count": len(self.checks),
            "passed": len(passed),
            "failed": len(failed),
            "errors": errors,
            "warnings": warnings,
            "remaining_failures": [c.name for c in failed],
            "check_details": [c.to_dict() for c in self.checks],
            "ts": time.time(),
        }


def hash_tree(root: Path, paths: List[str]) -> Dict[str, Any]:
    """对指定路径集合计算 SHA256 前缀哈希，用于检测状态漂移"""
    h = hashlib.sha256()
    seen = 0
    for rel in paths:
        base = root / rel
        if not base.exists():
            continue
        if base.is_file():
            files = [base]
        else:
            files = [p for p in base.rglob("*") if p.is_file() and "__pycache__" not in str(p)]
        for p in sorted(files):
            try:
                h.update(str(p.relative_to(root)).encode())
                h.update(p.read_bytes()[:4096])
                seen += 1
            except Exception:
                pass
    return {"sha256_prefix": h.hexdigest()[:24], "files_seen": seen}


def assert_no_external_api():
    """断言没有调用外部 API（用于测试）"""
    assert os.environ.get("NO_EXTERNAL_API") == "true", "NO_EXTERNAL_API 未设置"
    assert os.environ.get("NO_REAL_PAYMENT") == "true", "NO_REAL_PAYMENT 未设置"
    assert os.environ.get("NO_REAL_SEND") == "true", "NO_REAL_SEND 未设置"
    assert os.environ.get("NO_REAL_DEVICE") == "true", "NO_REAL_DEVICE 未设置"
