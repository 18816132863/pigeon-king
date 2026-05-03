#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 governance.fused_modules.probe_connected_runtime 导入
原脚本: scripts/probe_connected_runtime.py
"""
from __future__ import annotations

from governance.fused_modules.probe_connected_runtime import (
    check_call_device_tool_available,
    check_adapter_status,
    check_route_registry,
    check_safety_governor,
    probe_connected_runtime,
)


# Wrapper for: scripts/probe_connected_runtime.py
# Generated at: 2026-05-02 00:16:15