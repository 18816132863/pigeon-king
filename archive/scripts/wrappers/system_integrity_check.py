#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 governance.fused_modules.system_integrity_check 导入
原脚本: scripts/system_integrity_check.py
"""
from __future__ import annotations

from governance.fused_modules.system_integrity_check import (
    check_directories,
    check_files,
    check_tests,
    check_route_registry,
    main,
)


# Wrapper for: scripts/system_integrity_check.py
# Generated at: 2026-05-02 00:16:15