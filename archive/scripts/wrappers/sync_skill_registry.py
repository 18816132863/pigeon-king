#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 governance.fused_modules.sync_skill_registry 导入
原脚本: scripts/sync_skill_registry.py
"""
from __future__ import annotations

from governance.fused_modules.sync_skill_registry import (
    sync_skill_registry,
    sync_fusion_index,
    main,
)


# Wrapper for: scripts/sync_skill_registry.py
# Generated at: 2026-05-02 00:16:15