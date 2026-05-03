#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 governance.fused_modules.directory_fusion_and_cleanup 导入
原脚本: scripts/v99_directory_fusion_and_cleanup_gate.py
"""
from __future__ import annotations

from governance.fused_modules.directory_fusion_and_cleanup import (
    safe_jsonable,
    write_json,
    now,
    check_imports,
    classify_scripts,
    check_import_risk,
    main,
)


# Wrapper for: scripts/v99_directory_fusion_and_cleanup_gate.py
# Generated at: 2026-05-02 00:16:15