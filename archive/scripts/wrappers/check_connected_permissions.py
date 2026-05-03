#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.check_connected_permissions 导入
原脚本: scripts/check_connected_permissions.py
"""
from __future__ import annotations

from infrastructure.fused_modules.check_connected_permissions import (
    check_single_permission,
    check_all_permissions,
    get_permission_summary,
    get_missing_permission_hints,
    generate_report,
    main,
    PermissionChecker,
)


# Wrapper for: scripts/check_connected_permissions.py
# Generated at: 2026-05-02 00:16:15