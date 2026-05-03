#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.mainline_trigger 导入
原脚本: scripts/v99_mainline_trigger_gate.py
"""
from __future__ import annotations

from infrastructure.fused_modules.mainline_trigger import (
    safe_jsonable,
    write_json,
    now,
    record_trigger,
    run_scenario,
    scenario_1_offline_query,
    scenario_2_task_reminder,
    scenario_3_export_command,
    scenario_4_search_request,
    scenario_5_preference_update,
    scenario_6_scheduled_task,
    scenario_7_goal_with_sensitive_text,
    scenario_8_empty_goal,
    scenario_9_large_context,
    scenario_10_multiple_consecutive_triggers,
    main,
)


# Wrapper for: scripts/v99_mainline_trigger_gate.py
# Generated at: 2026-05-02 00:16:15