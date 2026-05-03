#!/usr/bin/env python3
"""
模块: check_repo_integrity
由融合引擎 V2 从 scripts/check_repo_integrity.py 自动生成
包含 16 个函数, 1 个类
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import subprocess
import pathlib
import argparse

ROOT = Path(__file__).resolve().parents[2]

def get_project_root(*args, **kwargs):

    ...

def check_file_exists(*args, **kwargs):

    """检查文件是否存在"""

def check_dir_exists(*args, **kwargs):

    """检查目录是否存在"""

def check_required_files(*args, **kwargs):

    """检查必需文件"""

def check_required_dirs(*args, **kwargs):

    """检查必需目录"""

def check_single_source_files(*args, **kwargs):

    """检查唯一真源文件"""

def check_schema_contracts(*args, **kwargs):

    """检查 Schema 与 Contract 对应关系"""

def check_rules_self_consistency(*args, **kwargs):

    """检查规则层自洽性"""

def check_makefile_targets(*args, **kwargs):

    """检查 Makefile 目标"""

def check_approval_history_consistency(*args, **kwargs):

    """检查审批历史与 remediation history 一致性"""

def run_layer_dependency_check(*args, **kwargs):

    """调用层间依赖检查"""

def run_json_contract_check(*args, **kwargs):

    """调用 JSON 契约检查"""

def run_rule_guards_self_test(*args, **kwargs):

    """调用规则守卫自测"""

def run_all_checks(*args, **kwargs):

    """运行所有检查"""


# Generated from: scripts/check_repo_integrity.py
# Generated at: 2026-05-02 00:16:15
