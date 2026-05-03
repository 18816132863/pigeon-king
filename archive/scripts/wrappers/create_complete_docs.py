#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.create_complete_docs 导入
原脚本: scripts/create_complete_docs.py
"""
from __future__ import annotations

from infrastructure.fused_modules.create_complete_docs import (
    add_chart_image,
    create_health_report_with_charts,
    create_diet_plan_with_nutrition,
)


# Wrapper for: scripts/create_complete_docs.py
# Generated at: 2026-05-02 00:16:15