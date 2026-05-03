#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 governance.fused_modules.smart_compressor 导入
原脚本: scripts/smart_compressor.py
"""
from __future__ import annotations

from governance.fused_modules.smart_compressor import (
    compress_json_smart,
    compress_markdown_smart,
    compress_file,
)


# Wrapper for: scripts/smart_compressor.py
# Generated at: 2026-05-02 00:16:15