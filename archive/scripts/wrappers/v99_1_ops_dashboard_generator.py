#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.1_ops_dashboard_generator 导入
原脚本: scripts/v99_1_ops_dashboard_generator.py
"""
from __future__ import annotations

from infrastructure.fused_modules.1_ops_dashboard_generator import (
    now,
    load_json,
    file_count,
    lines_count,
    gate_history,
    total_gates_passed,
    layers_stats,
    collect_system_metrics,
    build_dashboard,
    main,
)


# Wrapper for: scripts/v99_1_ops_dashboard_generator.py
# Generated at: 2026-05-02 00:16:15