#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.full_backup 导入
原脚本: scripts/full_backup.py
"""
from __future__ import annotations

from infrastructure.fused_modules.full_backup import (
    get_project_root,
    create_backup_manifest,
    copy_backup_files,
    create_backup_archive,
    run_backup,
    list_backups,
    main,
)


# Wrapper for: scripts/full_backup.py
# Generated at: 2026-05-02 00:16:15