#!/usr/bin/env python3
"""
向后兼容 wrapper — 从 infrastructure.fused_modules.check_repo_integrity 导入
原脚本: scripts/check_repo_integrity.py
"""
from __future__ import annotations

from infrastructure.fused_modules.check_repo_integrity import (
    get_project_root,
    check_file_exists,
    check_dir_exists,
    check_required_files,
    check_required_dirs,
    check_single_source_files,
    check_schema_contracts,
    check_rules_self_consistency,
    check_makefile_targets,
    check_approval_history_consistency,
    run_layer_dependency_check,
    run_json_contract_check,
    run_rule_guards_self_test,
    run_all_checks,
    main,
    RepoIntegrityChecker,
)


# Wrapper for: scripts/check_repo_integrity.py
# Generated at: 2026-05-02 00:16:15