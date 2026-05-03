#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.session_end_detector 导入
原脚本: scripts/session_end_detector.py
"""
from __future__ import annotations

from infrastructure.fused_modules.session_end_detector import (
    get_project_root,
    load_state,
    save_state,
    update_interaction,
    check_session_end,
    should_backup,
    mark_backup_done,
    run,
    main,
    SessionEndDetector,
)


# Wrapper for: scripts/session_end_detector.py
# Generated at: 2026-05-02 00:16:15