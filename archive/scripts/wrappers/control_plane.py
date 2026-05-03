#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.control_plane 导入
原脚本: scripts/control_plane.py
"""
from __future__ import annotations

from infrastructure.fused_modules.control_plane import (
    get_project_root,
    load_json,
    save_json,
    aggregate,
    build_control_plane_state,
    main,
    ControlPlaneAggregator,
)


# Wrapper for: scripts/control_plane.py
# Generated at: 2026-05-02 00:16:15