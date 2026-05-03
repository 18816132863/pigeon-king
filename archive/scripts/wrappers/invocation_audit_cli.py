#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.invocation_audit_cli 导入
原脚本: scripts/invocation_audit_cli.py
"""
from __future__ import annotations

from infrastructure.fused_modules.invocation_audit_cli import (
    redact_value,
    redact_json_string,
    redact_sensitive,
    cmd_query_recent,
    cmd_query_uncertain,
    cmd_query_failed,
    cmd_query_timeout,
    cmd_confirm,
    cmd_stats,
    cmd_breakdown,
    cmd_seed_demo,
    cmd_export,
    cmd_cleanup,
    print_table,
    print_csv,
    records_to_csv,
    main,
)


# Wrapper for: scripts/invocation_audit_cli.py
# Generated at: 2026-05-02 00:16:15