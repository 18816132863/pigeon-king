#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 governance.fused_modules.2_all_chain_coverage 导入
原脚本: scripts/v95_2_all_chain_coverage_gate.py
"""
from __future__ import annotations

from governance.fused_modules.2_all_chain_coverage import (
    safe_jsonable,
    write_json,
    import_module_path,
    run_step,
    main,
)


# Wrapper for: scripts/v95_2_all_chain_coverage_gate.py
# Generated at: 2026-05-02 00:16:15