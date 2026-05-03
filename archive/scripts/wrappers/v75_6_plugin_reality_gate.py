#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 governance.fused_modules.6_plugin_reality 导入
原脚本: scripts/v75_6_plugin_reality_gate.py
"""
from __future__ import annotations

from governance.fused_modules.6_plugin_reality import (
    check_scripts_directory,
    check_install_check_report,
    check_no_false_positives,
    check_plugin_binaries_status,
    check_version_label,
    main,
)


# Wrapper for: scripts/v75_6_plugin_reality_gate.py
# Generated at: 2026-05-02 00:16:15