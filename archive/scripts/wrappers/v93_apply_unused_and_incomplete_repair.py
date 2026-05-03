#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.apply_unused_and_incomplete_repair 导入
原脚本: scripts/v93_apply_unused_and_incomplete_repair.py
"""
from __future__ import annotations

from infrastructure.fused_modules.apply_unused_and_incomplete_repair import (
    safe_jsonable,
    write_json,
    import_status,
    dry_run_module,
    ensure_local_state,
    dependency_fallbacks,
    external_infra_fallbacks,
    archive_candidates,
    main,
)


# Wrapper for: scripts/v93_apply_unused_and_incomplete_repair.py
# Generated at: 2026-05-02 00:16:15