#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 memory_context.fused_modules.generate_metrics 导入
原脚本: scripts/generate_metrics.py
"""
from __future__ import annotations

from memory_context.fused_modules.generate_metrics import (
    generate_task_metrics,
    generate_skill_metrics,
    generate_memory_metrics,
    generate_aggregated_report,
    main,
)


# Wrapper for: scripts/generate_metrics.py
# Generated at: 2026-05-02 00:16:15