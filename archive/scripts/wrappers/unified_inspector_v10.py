#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 core.fused_modules.unified_inspector_v10 导入
原脚本: scripts/unified_inspector_v10.py
"""
from __future__ import annotations

from core.fused_modules.unified_inspector_v10 import (
    get_project_root,
    check_file_exists,
    check_dir_exists,
    check_json_valid,
    check_import,
    check_function_exists,
    check_class_exists,
    get_system_stats,
    check_system,
    check_layers,
    check_module,
    check_v85_modules,
    check_llm_engine,
    check_security_boundaries,
    check_reports,
    check_infrastructure,
    run_all,
    save_json_report,
    generate_html_report,
    main,
    V10Inspector,
)


# Wrapper for: scripts/unified_inspector_v10.py
# Generated at: 2026-05-02 00:16:15