#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.check_route_wiring 导入
原脚本: scripts/check_route_wiring.py
"""
from __future__ import annotations

from infrastructure.fused_modules.check_route_wiring import (
    scan_routes,
    scan_registered_capabilities,
    scan_registered_skills,
    check_wiring,
    run_check,
    save_report,
    main,
    RouteWiringChecker,
)


# Wrapper for: scripts/check_route_wiring.py
# Generated at: 2026-05-02 00:16:15