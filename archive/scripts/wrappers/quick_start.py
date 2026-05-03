#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 governance.fused_modules.quick_start 导入
原脚本: scripts/quick_start.py
"""
from __future__ import annotations

from governance.fused_modules.quick_start import (
    load_core_files,
    load_file,
    load_skill_registry,
    startup,
    QuickStart,
)


# Wrapper for: scripts/quick_start.py
# Generated at: 2026-05-02 00:16:15