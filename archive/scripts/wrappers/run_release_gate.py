#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 governance.fused_modules.run_release 导入
原脚本: scripts/run_release_gate.py
"""
from __future__ import annotations

from governance.fused_modules.run_release import (
    get_project_root,
    run_command,
    run_rule_checks,
    print_rule_summary,
    print_change_impact_summary,
    record_executed_command,
    save_executed_checks,
    save_followup_requirements,
    save_enforcement_report,
    check_impact_enforcement,
    print_impact_enforcement_summary,
    run_expire_check,
    check_exception_constraints,
    verify_premerge,
    verify_nightly,
    verify_release,
)


# Wrapper for: scripts/run_release_gate.py
# Generated at: 2026-05-02 00:16:15