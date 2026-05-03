#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.run_daily_growth_check 导入
原脚本: scripts/run_daily_growth_check.py
"""
from __future__ import annotations

from infrastructure.fused_modules.run_daily_growth_check import (
    get_project_root,
    load_json,
    get_current_phase,
    run,
    main,
    DailyGrowthCheck,
)


# Wrapper for: scripts/run_daily_growth_check.py
# Generated at: 2026-05-02 00:16:15