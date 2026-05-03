#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
RESULT = ROOT / "V197_V226_PRODUCTION_CONTROL_PLANE_UPGRADE_RESULT.txt"

REQUIRED = [
    "core/production_control_plane/__init__.py",
    "core/production_control_plane/schemas.py",
    "core/production_control_plane/v197_system_registry.py",
    "core/production_control_plane/v198_workspace_tenant_manager.py",
    "core/production_control_plane/v199_role_access_matrix.py",
    "core/production_control_plane/v200_policy_pack_manager.py",
    "core/production_control_plane/v201_event_sourcing_ledger.py",
    "core/production_control_plane/v202_data_lineage_tracker.py",
    "core/production_control_plane/v203_backup_restore_verifier.py",
    "core/production_control_plane/v204_disaster_recovery_planner.py",
    "core/production_control_plane/v205_canary_deployment_controller.py",
    "core/production_control_plane/v206_feature_flag_manager.py",
    "core/production_control_plane/v207_model_canary_evaluator.py",
    "core/production_control_plane/v208_provider_failover_controller.py",
    "core/production_control_plane/v209_connector_quota_manager.py",
    "core/production_control_plane/v210_sla_escalation_router.py",
    "core/production_control_plane/v211_anomaly_detector.py",
    "core/production_control_plane/v212_capacity_planner.py",
    "core/production_control_plane/v213_dependency_graph_builder.py",
    "core/production_control_plane/v214_change_impact_analyzer.py",
    "core/production_control_plane/v215_contract_test_runner.py",
    "core/production_control_plane/v216_golden_path_validator.py",
    "core/production_control_plane/v217_user_acceptance_gate.py",
    "core/production_control_plane/v218_playbook_library.py",
    "core/production_control_plane/v219_runbook_executor.py",
    "core/production_control_plane/v220_training_data_curator.py",
    "core/production_control_plane/v221_review_workflow.py",
    "core/production_control_plane/v222_postmortem_generator.py",
    "core/production_control_plane/v223_governance_board.py",
    "core/production_control_plane/v224_objective_alignment.py",
    "core/production_control_plane/v225_roi_analyzer.py",
    "core/production_control_plane/v226_production_control_plane_kernel.py",
    "agent_kernel/production_control_plane.py",
]


def clean_cache() -> int:
    count = 0
    for p in list(ROOT.rglob("__pycache__")) + list(ROOT.rglob(".pytest_cache")):
        try:
            shutil.rmtree(p)
            count += 1
        except Exception:
            pass
    for p in list(ROOT.rglob("*.pyc")):
        try:
            p.unlink()
            count += 1
        except Exception:
            pass
    return count


def main() -> int:
    lines = [
        "V197-V226 PRODUCTION CONTROL PLANE UPGRADE RESULT",
        "=" * 80,
        f"Time: {datetime.now().isoformat(timespec='seconds')}",
        f"Root: {ROOT}",
        "",
    ]
    ok = True
    lines.append(f"Cache cleaned: {clean_cache()}")

    missing = [x for x in REQUIRED if not (ROOT / x).exists()]
    if missing:
        ok = False
        lines.append("Required files: FAIL")
        lines.extend([f"  - {m}" for m in missing])
    else:
        lines.append("Required files: PASS")

    try:
        from core.production_control_plane import init_production_control_plane, run_production_control_plane_cycle
        init = init_production_control_plane(".v197_v226_state")
        lines.append(f"Init production control plane: PASS => {init}")

        r = run_production_control_plane_cycle("继续推进生产控制平面30个版本，给压缩包和命令", root=".v197_v226_state")
        lines.append(
            f"Cycle: {r.status.value} | completed_versions={r.completed_versions} | "
            f"artifacts={r.artifact_count} | readiness={r.readiness_score} | gate={r.gate_decision.value}"
        )
        lines.append(f"Dashboard: {r.dashboard_summary}")
        if r.completed_versions != 30 or r.artifact_count < 29 or r.readiness_score <= 0:
            ok = False
            lines.append("Cycle check: FAIL")
    except Exception as e:
        ok = False
        lines.append("Runtime verification: FAIL")
        lines.append(repr(e))

    lines.append(f"Final cache cleanup: {clean_cache()}")
    lines.append("")
    lines.append("PASS: V197-V226 production control plane upgrade applied and verified." if ok else "FAIL: V197-V226 production control plane upgrade has blocking issues.")
    RESULT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
