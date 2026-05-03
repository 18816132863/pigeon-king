#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.6_plugin_install_check 导入
原脚本: scripts/v75_6_plugin_install_check.py
"""
from __future__ import annotations

from infrastructure.fused_modules.6_plugin_install_check import (
    run_command,
    get_openclaw_plugins,
    check_better_gateway,
    check_lobster,
    check_node_pty,
    check_single_plugin,
    check_scripts_exist,
    main,
    PluginInstallStatus,
    PluginCheckResult,
    PluginInstallReport,
)


# Wrapper for: scripts/v75_6_plugin_install_check.py
# Generated at: 2026-05-02 00:16:15