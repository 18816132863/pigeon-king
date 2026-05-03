#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.generate_charts 导入
原脚本: scripts/generate_charts.py
"""
from __future__ import annotations

from infrastructure.fused_modules.generate_charts import (
    create_sleep_trend_chart,
    create_steps_bar_chart,
    create_exercise_pie_chart,
    create_health_radar_chart,
)


# Wrapper for: scripts/generate_charts.py
# Generated at: 2026-05-02 00:16:15