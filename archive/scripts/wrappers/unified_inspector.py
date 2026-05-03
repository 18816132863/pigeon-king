#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.unified_inspector 导入
原脚本: scripts/unified_inspector.py
"""
from __future__ import annotations

from infrastructure.fused_modules.unified_inspector import (
    get_project_root,
    get_file_hash_fast,
    load_cache_fast,
    save_cache_fast,
    run_check_fast,
    check_token_optimization,
    check_injection_config,
    run_all_checks_fast,
    print_summary_fast,
    save_report_fast,
    main,
)


# Wrapper for: scripts/unified_inspector.py
# Generated at: 2026-05-02 00:16:15