#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 memory_context.fused_modules.mainline_trigger 导入
原脚本: scripts/v94_mainline_trigger_gate.py
"""
from __future__ import annotations

from memory_context.fused_modules.mainline_trigger import (
    safe_jsonable,
    write_json,
    now,
    trigger_module,
    main,
    pkg,
    pem,
    sil,
    mwg,
    ss,
    idg,
    obs,
    cesg,
    cm,
    dag,
)


# Wrapper for: scripts/v94_mainline_trigger_gate.py
# Generated at: 2026-05-02 00:16:15