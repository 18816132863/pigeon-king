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
RESULT = ROOT / "V227_V256_AUTONOMOUS_RUNTIME_FABRIC_UPGRADE_RESULT.txt"

REQUIRED = [
    "core/autonomous_runtime_fabric/__init__.py",
    "core/autonomous_runtime_fabric/schemas.py",
    "core/autonomous_runtime_fabric/v227_control_tower.py",
    "core/autonomous_runtime_fabric/v228_runtime_mesh_registry.py",
    "core/autonomous_runtime_fabric/v229_service_discovery.py",
    "core/autonomous_runtime_fabric/v230_config_overlay_manager.py",
    "core/autonomous_runtime_fabric/v231_secret_reference_vault.py",
    "core/autonomous_runtime_fabric/v232_policy_enforcement_point.py",
    "core/autonomous_runtime_fabric/v233_tool_broker.py",
    "core/autonomous_runtime_fabric/v234_workflow_template_registry.py",
    "core/autonomous_runtime_fabric/v235_execution_lease_manager.py",
    "core/autonomous_runtime_fabric/v236_state_checkpoint_graph.py",
    "core/autonomous_runtime_fabric/v237_replay_lab.py",
    "core/autonomous_runtime_fabric/v238_deterministic_verifier.py",
    "core/autonomous_runtime_fabric/v239_self_healing_planner.py",
    "core/autonomous_runtime_fabric/v240_degradation_controller.py",
    "core/autonomous_runtime_fabric/v241_alert_router.py",
    "core/autonomous_runtime_fabric/v242_trust_zone_manager.py",
    "core/autonomous_runtime_fabric/v243_artifact_signer.py",
    "core/autonomous_runtime_fabric/v244_dependency_lockfile_builder.py",
    "core/autonomous_runtime_fabric/v245_cache_coordinator.py",
    "core/autonomous_runtime_fabric/v246_queue_shard_planner.py",
    "core/autonomous_runtime_fabric/v247_resource_forecast_engine.py",
    "core/autonomous_runtime_fabric/v248_model_fleet_manager.py",
    "core/autonomous_runtime_fabric/v249_memory_tier_manager.py",
    "core/autonomous_runtime_fabric/v250_evidence_bundle_builder.py",
    "core/autonomous_runtime_fabric/v251_run_replay_exporter.py",
    "core/autonomous_runtime_fabric/v252_operator_console.py",
    "core/autonomous_runtime_fabric/v253_integration_smoke_test.py",
    "core/autonomous_runtime_fabric/v254_security_posture_review.py",
    "core/autonomous_runtime_fabric/v255_fabric_readiness_board.py",
    "core/autonomous_runtime_fabric/v256_autonomous_runtime_fabric_kernel.py",
    "agent_kernel/autonomous_runtime_fabric.py",
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
        "V227-V256 AUTONOMOUS RUNTIME FABRIC UPGRADE RESULT",
        "=" * 82,
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
        from core.autonomous_runtime_fabric import init_autonomous_runtime_fabric, run_autonomous_runtime_fabric_cycle
        init = init_autonomous_runtime_fabric(".v227_v256_state")
        lines.append(f"Init autonomous runtime fabric: PASS => {init}")

        r = run_autonomous_runtime_fabric_cycle("继续推进自愈运行织网30个版本，给压缩包和命令", root=".v227_v256_state")
        lines.append(
            f"Cycle: {r.status.value} | completed_versions={r.completed_versions} | "
            f"artifacts={r.artifact_count} | readiness={r.readiness_score} | gate={r.gate.value}"
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
    lines.append("PASS: V227-V256 autonomous runtime fabric upgrade applied and verified." if ok else "FAIL: V227-V256 autonomous runtime fabric upgrade has blocking issues.")
    RESULT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
