#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 execution.fused_modules.heartbeat_executor 导入
原脚本: scripts/heartbeat_executor.py
"""
from __future__ import annotations

from execution.fused_modules.heartbeat_executor import (
    get_project_root,
    run_task,
    run_all,
    main,
    HeartbeatExecutor,
)


# Wrapper for: scripts/heartbeat_executor.py
# Generated at: 2026-05-02 00:16:15