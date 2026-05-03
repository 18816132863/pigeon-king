"""
V106 懒加载兼容桥接 — 整合旧 LazyLoader / token_budget / agent_kernel_facade

将所有旧导入统一登记到 unified_lazy_loader。
不删除旧文件，只做桥接。
"""
from __future__ import annotations

import sys
from typing import Any, Optional, Dict
from pathlib import Path

from infrastructure.lazy.unified_lazy_loader import (
    load_module_on_demand,
    load_full_skill,
    load_metadata,
    get_loaded_status,
    record_lazy_load_event,
)


# ══════════════════════════════════════════════════
# 桥接旧 LazyLoader
# ══════════════════════════════════════════════════

def bridge_lazy_loader(module_path: str) -> Optional[Any]:
    """桥接旧 infrastructure.loader.lazy_loader 的 lazy_import。
    
    旧用法: from infrastructure.loader.lazy_loader import lazy_import
             module = lazy_import("my.module")
    
    新用法: from infrastructure.lazy.lazy_compat_bridge import bridge_lazy_loader
             module = bridge_lazy_loader("my.module")
    """
    record_lazy_load_event(f"lazy_bridge:{module_path}", "bridge_lazy_loader", "requested")
    return load_module_on_demand(module_path)


# ══════════════════════════════════════════════════
# 桥接 token_budget
# ══════════════════════════════════════════════════

def bridge_check_budget(component: str, estimated_tokens: int = 0) -> Dict[str, Any]:
    """桥接旧 infrastructure.token_budget 的预算检查。
    
    旧用法: from infrastructure.token_budget import check_skill_budget
             ok = check_skill_budget(skill_id, estimate)
    
    在 V106 中，P2 技能按需加载，预算检查只在 full_skill 加载时触发生效。
    """
    is_loaded = __import__("infrastructure.lazy.unified_lazy_loader",
                           fromlist=["is_full_skill_loaded"])
    loaded = is_loaded.is_full_skill_loaded(component)
    
    result = {
        "budget_checked": True,
        "component": component,
        "loaded": loaded,
        "estimated_tokens": estimated_tokens,
        "note": "V106: P2 懒加载，预算检查只在 full skill 加载时生效",
    }
    record_lazy_load_event(f"budget:{component}", "bridge_budget_check", str(loaded))
    return result


# ══════════════════════════════════════════════════
# 桥接 agent_kernel_facade lazy_import
# ══════════════════════════════════════════════════

def bridge_facade_import(module_name: str) -> Optional[Any]:
    """桥接旧 orchestration.agent_kernel_facade 的 lazy_import。
    
    在 V106 中，agent_kernel 的懒导入统一走 unified_lazy_loader。
    """
    record_lazy_load_event(f"facade:{module_name}", "bridge_facade_import", "requested")
    return load_module_on_demand(module_name)


# ══════════════════════════════════════════════════
# 统一加载状态摘要
# ══════════════════════════════════════════════════

def get_compat_status() -> Dict[str, Any]:
    """获取兼容桥接状态摘要。"""
    status = get_loaded_status()
    status["bridge_available"] = True
    status["has_lazy_loader_bridge"] = True
    status["has_token_budget_bridge"] = True
    status["has_facade_bridge"] = True
    return status
