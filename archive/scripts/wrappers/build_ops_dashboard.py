#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.build_ops_dashboard 导入
原脚本: scripts/build_ops_dashboard.py
"""
from __future__ import annotations

from infrastructure.fused_modules.build_ops_dashboard import (
    get_project_root,
    load_json,
    load_latest_reports,
    load_history_snapshots,
    build_overview_section,
    build_runtime_section,
    build_quality_section,
    build_release_section,
    build_alerts_section,
    build_incidents_section,
    build_trends_section,
    build_recent_changes_section,
    build_dashboard,
    generate_markdown,
    generate_html,
    save_dashboard,
    main,
)


# Wrapper for: scripts/build_ops_dashboard.py
# Generated at: 2026-05-02 00:16:14