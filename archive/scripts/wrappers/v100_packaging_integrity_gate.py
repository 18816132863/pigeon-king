#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 governance.fused_modules.packaging_integrity 导入
原脚本: scripts/v100_packaging_integrity_gate.py
"""
from __future__ import annotations

from governance.fused_modules.packaging_integrity import (
    safe_jsonable,
    now,
    norm_path,
    check_required_paths,
    check_excluded_paths,
    check_rebuildable_paths,
    check_root_cleanliness,
    check_gates_preserved,
    check_state_dirs,
    main,
)


# Wrapper for: scripts/v100_packaging_integrity_gate.py
# Generated at: 2026-05-02 00:16:15