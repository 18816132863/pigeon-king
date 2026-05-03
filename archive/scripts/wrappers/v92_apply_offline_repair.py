#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.apply_offline_repair 导入
原脚本: scripts/v92_apply_offline_repair.py
"""
from __future__ import annotations

from infrastructure.fused_modules.apply_offline_repair import (
    now,
    write_json,
    audit,
    ensure_init,
    pyfile,
    patch_drift_status,
    ensure_personal_knowledge_graph,
    ensure_preference_evolution,
    ensure_memory_writeback_guard,
    ensure_self_improvement_loop,
    ensure_offline_solution_search,
    ensure_registries,
    patch_gateway_solution_search,
    run_smoke,
    main,
)


# Wrapper for: scripts/v92_apply_offline_repair.py
# Generated at: 2026-05-02 00:16:15