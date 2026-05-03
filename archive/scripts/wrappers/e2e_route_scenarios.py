#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 orchestration.fused_modules.e2e_route_scenarios 导入
原脚本: scripts/e2e_route_scenarios.py
"""
from __future__ import annotations

from orchestration.fused_modules.e2e_route_scenarios import (
    run_scenario,
    run_all_scenarios,
    main,
    E2EScenarioRunner,
)


# Wrapper for: scripts/e2e_route_scenarios.py
# Generated at: 2026-05-02 00:16:15