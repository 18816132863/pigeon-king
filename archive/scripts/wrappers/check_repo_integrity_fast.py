#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 governance.fused_modules.check_repo_integrity_fast 导入
原脚本: scripts/check_repo_integrity_fast.py
"""
from __future__ import annotations

from governance.fused_modules.check_repo_integrity_fast import (
    get_project_root,
    check_file,
    check_dir,
    main,
)


# Wrapper for: scripts/check_repo_integrity_fast.py
# Generated at: 2026-05-02 00:16:15