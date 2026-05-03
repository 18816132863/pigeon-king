#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.run_daily_growth_loop 导入
原脚本: scripts/run_daily_growth_loop.py
"""
from __future__ import annotations

from infrastructure.fused_modules.run_daily_growth_loop import (
    get_project_root,
    load_json,
    save_json,
    append_jsonl,
    check_today_started,
    get_today_state,
    load_top10_tasks,
    load_priority_order,
    select_tasks,
    generate_daily_plan,
    run,
    main,
    DailyGrowthLoop,
)


# Wrapper for: scripts/run_daily_growth_loop.py
# Generated at: 2026-05-02 00:16:15