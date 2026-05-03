#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.apply_identity_context_stability 导入
原脚本: scripts/v98_apply_identity_context_stability.py
"""
from __future__ import annotations

from infrastructure.fused_modules.apply_identity_context_stability import (
    backup,
    upsert_block,
    write_if_missing,
    merge_openclaw_json,
    append_jsonl,
    main,
)


# Wrapper for: scripts/v98_apply_identity_context_stability.py
# Generated at: 2026-05-02 00:16:15