#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.control_plane_audit 导入
原脚本: scripts/control_plane_audit.py
"""
from __future__ import annotations

from infrastructure.fused_modules.control_plane_audit import (
    get_project_root,
    load_json,
    load_json_list,
    save_json,
    aggregate,
    build_control_plane_audit,
    main,
    ControlPlaneAuditAggregator,
)


# Wrapper for: scripts/control_plane_audit.py
# Generated at: 2026-05-02 00:16:15