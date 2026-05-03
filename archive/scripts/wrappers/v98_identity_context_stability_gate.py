#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 governance.fused_modules.identity_context_stability 导入
原脚本: scripts/v98_identity_context_stability_gate.py
"""
from __future__ import annotations

from governance.fused_modules.identity_context_stability import (
    read,
    sha_text,
    load_json,
    check_project_context,
    check_openclaw,
    check_lobster,
    memory_pressure,
    check_previous_gates,
    env_flags,
    main,
)


# Wrapper for: scripts/v98_identity_context_stability_gate.py
# Generated at: 2026-05-02 00:16:15