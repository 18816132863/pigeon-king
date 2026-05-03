#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.run_nightly_audit 导入
原脚本: scripts/run_nightly_audit.py
"""
from __future__ import annotations

from infrastructure.fused_modules.run_nightly_audit import (
    get_project_root,
    load_latest_report,
    load_previous_report,
    compare_runtime_reports,
    compare_quality_reports,
    compare_release_reports,
    check_skill_registry_changes,
    check_p2_trend,
    generate_audit_report,
    generate_summary_md,
    update_trend,
    run_nightly_audit,
)


# Wrapper for: scripts/run_nightly_audit.py
# Generated at: 2026-05-02 00:16:15