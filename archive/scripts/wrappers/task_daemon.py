#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.task_daemon 导入
原脚本: scripts/task_daemon.py
"""
from __future__ import annotations

from infrastructure.fused_modules.task_daemon import (
    start,
    stop,
    main,
    TaskDaemon,
)


# Wrapper for: scripts/task_daemon.py
# Generated at: 2026-05-02 00:16:15