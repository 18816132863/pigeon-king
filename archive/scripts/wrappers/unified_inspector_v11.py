#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.unified_inspector_v11 导入
原脚本: scripts/unified_inspector_v11.py
"""
from __future__ import annotations

from infrastructure.fused_modules.unified_inspector_v11 import (
    get_project_root,
    check_dir_exists,
    check_file_exists,
    check_json_valid,
    get_system_stats,
    check_system,
    check_layers,
    check_v99_fusion,
    check_infrastructure_modules,
    check_v85_modules,
    check_knowledge_graph,
    check_gate_reports,
    check_llm_engine,
    run_all,
    save_json_report,
    main,
    V11Inspector,
)


# Wrapper for: scripts/unified_inspector_v11.py
# Generated at: 2026-05-02 00:16:15