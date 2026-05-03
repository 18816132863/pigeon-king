#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 governance.fused_modules.long_run_stability 导入
原脚本: scripts/v97_long_run_stability_gate.py
"""
from __future__ import annotations

from governance.fused_modules.long_run_stability import (
    safe_jsonable,
    write_json,
    now,
    compute_state_hash,
    detect_changes,
    record_run,
    run_v95_2,
    run_v96,
    build_entry,
    main,
)


# Wrapper for: scripts/v97_long_run_stability_gate.py
# Generated at: 2026-05-02 00:16:15