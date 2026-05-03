#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.full_static_audit_and_repair 导入
原脚本: scripts/v92_full_static_audit_and_repair_gate.py
"""
from __future__ import annotations

from infrastructure.fused_modules.full_static_audit_and_repair import (
    now,
    write_json,
    read_json,
    check_no_external_api_env,
    import_status,
    run_apply_if_needed,
    main,
)


# Wrapper for: scripts/v92_full_static_audit_and_repair_gate.py
# Generated at: 2026-05-02 00:16:15