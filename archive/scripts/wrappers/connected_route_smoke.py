#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.connected_route 导入
原脚本: scripts/connected_route_smoke.py
"""
from __future__ import annotations

from infrastructure.fused_modules.connected_route import (
    setup,
    check_device_state,
    test_safe_routes,
    test_confirm_routes,
    test_strong_confirm_routes,
    generate_report,
    main,
    ConnectedRouteSmokeTest,
)


# Wrapper for: scripts/connected_route_smoke.py
# Generated at: 2026-05-02 00:16:15