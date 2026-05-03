"""
V106 统一懒加载器

支持：
- load_metadata(skill_id) — 只加载技能元数据
- load_full_skill(skill_id) — 用户确认后加载完整 skill
- load_module_on_demand(module_path) — 按需导入模块
- get_loaded_status() — 获取当前加载状态
- fallback_to_mock(reason) — 降级为 mock
- record_lazy_load_event() — 记录加载事件

所有加载事件写入 .lazy_state/lazy_load_ledger.jsonl
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from infrastructure.lazy.unified_lazy_loading_policy import (
    LazyLoadRule,
    LoadPriority,
    get_rule,
    get_p0_names,
    get_p2_names,
    is_security_related,
    should_block_in_offline,
)

ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY = ROOT / "governance" / "skill_trigger_registry.json"
LazyStateDir = ROOT / ".lazy_state"
LazyLedger = LazyStateDir / "lazy_load_ledger.jsonl"


# ══════════════════════════════════════════════════
# 内部状态
# ══════════════════════════════════════════════════

_loaded_set: Set[str] = set()          # 已加载的组件名
_loaded_modules: Set[str] = set()      # 已 import 的模块路径
_preloaded: bool = False               # P0 是否已加载
_mock_fallbacks: Dict[str, str] = []   # 降级为 mock 的组件

OFFLINE = os.environ.get("NO_EXTERNAL_API") == "true"


# ══════════════════════════════════════════════════
# 记录器
# ══════════════════════════════════════════════════

def _ensure_ledger():
    LazyStateDir.mkdir(parents=True, exist_ok=True)


def record_lazy_load_event(
    component: str,
    action: str,
    status: str,
    duration_ms: float = 0.0,
    detail: str = "",
) -> None:
    """记录一个懒加载事件到 ledger。"""
    _ensure_ledger()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": component,
        "action": action,
        "status": status,
        "duration_ms": round(duration_ms, 2),
        "detail": detail,
    }
    with open(LazyLedger, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_lazy_load_ledger(limit: int = 50) -> List[Dict[str, Any]]:
    """读取最近的懒加载事件。"""
    if not LazyLedger.exists():
        return []
    entries = []
    with open(LazyLedger, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except Exception:
                    pass
    return entries[-limit:]


# ══════════════════════════════════════════════════
# 核心加载函数
# ══════════════════════════════════════════════════

def preload_p0() -> bool:
    """预加载 P0 安全/人格核心组件。
    
    安全规则和人格上下文永远不懒加载。
    """
    global _preloaded
    if _preloaded:
        return True
    
    p0_names = get_p0_names()
    for name in p0_names:
        rule = get_rule(name)
        if not rule:
            continue
        start = time.time()
        try:
            # Mark as loaded (actual data will be loaded by the caller)
            _loaded_set.add(name)
            elapsed = (time.time() - start) * 1000
            record_lazy_load_event(name, "preload_p0", "loaded", elapsed)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            record_lazy_load_event(name, "preload_p0", "failed", elapsed, str(e))
    
    _preloaded = True
    return True


def load_metadata(skill_id: str) -> Optional[Dict[str, Any]]:
    """只加载技能的元数据（来自 skill_trigger_registry.json）。"""
    start = time.time()
    if not REGISTRY.exists():
        record_lazy_load_event(f"skill:{skill_id}", "load_metadata", "failed", detail="registry not found")
        return None
    
    try:
        registry_data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        meta = registry_data.get(skill_id)
        if meta:
            _loaded_set.add(f"skill_meta:{skill_id}")
            elapsed = (time.time() - start) * 1000
            record_lazy_load_event(f"skill:{skill_id}", "load_metadata", "loaded", elapsed)
            return meta
        record_lazy_load_event(f"skill:{skill_id}", "load_metadata", "not_found", detail="not in registry")
        return None
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        record_lazy_load_event(f"skill:{skill_id}", "load_metadata", "failed", elapsed, str(e))
        return None


def load_full_skill(skill_id: str) -> Optional[Dict[str, Any]]:
    """用户确认后加载完整 SKILL.md。"""
    start = time.time()
    skill_dir = ROOT / "skills" / skill_id
    skill_md = skill_dir / "SKILL.md"
    
    if not skill_md.exists():
        record_lazy_load_event(f"skill:{skill_id}", "load_full_skill", "not_found")
        return None
    
    try:
        # Check if this skill should be blocked in offline mode
        rule = get_rule(skill_id)
        if rule and rule.requires_external and OFFLINE:
            elapsed = (time.time() - start) * 1000
            record_lazy_load_event(f"skill:{skill_id}", "load_full_skill", "blocked_offline", elapsed)
            return {"status": "blocked", "reason": "skill requires external API, blocked in offline mode"}
        
        # Read full SKILL.md
        full_text = skill_md.read_text(encoding="utf-8", errors="ignore")
        _loaded_set.add(f"skill_full:{skill_id}")
        
        # Also read trigger_keywords from registry
        meta = load_metadata(skill_id)
        
        result = {
            "status": "loaded",
            "skill_id": skill_id,
            "full_text": full_text,
            "trigger_keywords": (meta or {}).get("trigger_keywords", []),
            "requires_external_api": (meta or {}).get("requires_external_api", False),
        }
        elapsed = (time.time() - start) * 1000
        record_lazy_load_event(f"skill:{skill_id}", "load_full_skill", "loaded", elapsed)
        return result
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        record_lazy_load_event(f"skill:{skill_id}", "load_full_skill", "failed", elapsed, str(e))
        return None


def load_module_on_demand(module_path: str) -> Optional[Any]:
    """按需导入模块。"""
    start = time.time()
    if module_path in _loaded_modules:
        return None  # Already loaded
    
    try:
        __import__(module_path)
        _loaded_modules.add(module_path)
        elapsed = (time.time() - start) * 1000
        record_lazy_load_event(f"module:{module_path}", "on_demand_import", "loaded", elapsed)
        return sys.modules.get(module_path)
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        record_lazy_load_event(f"module:{module_path}", "on_demand_import", "failed", elapsed, str(e))
        return None


def fallback_to_mock(component: str, reason: str = "") -> bool:
    """将指定组件降级为 mock 模式。"""
    start = time.time()
    _mock_fallbacks.append({
        "component": component,
        "reason": reason or "fallback by policy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    _loaded_set.add(f"mock:{component}")
    elapsed = (time.time() - start) * 1000
    record_lazy_load_event(f"mock:{component}", "fallback_to_mock", "fallback", elapsed, reason)
    return True


def get_loaded_status() -> Dict[str, Any]:
    """获取当前懒加载状态。"""
    return {
        "preloaded": _preloaded,
        "p0_loaded": [n for n in _loaded_set if n.startswith(("V90", "V92", "V100", "offline", "mainline", "AGENTS.md", "IDENTITY.md", "MEMORY.md", "CURRENT_"))],
        "skill_metadata_loaded": [n for n in _loaded_set if n.startswith("skill_meta:")],
        "skill_full_loaded": [n for n in _loaded_set if n.startswith("skill_full:")],
        "modules_imported": list(_loaded_modules),
        "mock_fallbacks": _mock_fallbacks,
        "total_loaded": len(_loaded_set),
        "ledger_entries": LazyLedger.exists(),
    }


def is_preloaded() -> bool:
    """检查 P0 是否已预加载。"""
    return _preloaded


def is_full_skill_loaded(skill_id: str) -> bool:
    """检查某个技能是否已完成完整加载。"""
    return f"skill_full:{skill_id}" in _loaded_set


def is_metadata_loaded(skill_id: str) -> bool:
    """检查某个技能的元数据是否已加载。"""
    return f"skill_meta:{skill_id}" in _loaded_set


# ══════════════════════════════════════════════════
# 启动时自动预加载 P0
# ══════════════════════════════════════════════════

preload_p0()
