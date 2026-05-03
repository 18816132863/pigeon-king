#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.health_watch 导入
原脚本: scripts/health_watch.py
"""
from __future__ import annotations

from infrastructure.fused_modules.health_watch import (
    check_disk,
    check_memory,
    check_gateway,
    check_imports,
    check_daemon,
    snapshot,
    diff_state,
    log_alert,
    load_previous,
    run_once,
    main,
)


# Wrapper for: scripts/health_watch.py
# Generated at: 2026-05-02 00:14:56