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
RESULT = ROOT / "V167_V196_OPERATIONS_INTELLIGENCE_UPGRADE_RESULT.txt"

REQUIRED = [
    "core/operations_intelligence/__init__.py",
    "core/operations_intelligence/schemas.py",
    "core/operations_intelligence/v167_roadmap_planner.py",
    "core/operations_intelligence/v168_portfolio_manager.py",
    "core/operations_intelligence/v169_experiment_designer.py",
    "core/operations_intelligence/v170_metrics_kpi_engine.py",
    "core/operations_intelligence/v171_data_ingestion_hub.py",
    "core/operations_intelligence/v172_data_quality_gate.py",
    "core/operations_intelligence/v173_report_generator.py",
    "core/operations_intelligence/v174_decision_memo_builder.py",
    "core/operations_intelligence/v175_risk_register.py",
    "core/operations_intelligence/v176_incident_manager.py",
    "core/operations_intelligence/v177_slo_manager.py",
    "core/operations_intelligence/v178_cost_analyzer.py",
    "core/operations_intelligence/v179_performance_profiler.py",
    "core/operations_intelligence/v180_token_optimizer.py",
    "core/operations_intelligence/v181_prompt_policy_compiler.py",
    "core/operations_intelligence/v182_eval_dataset_builder.py",
    "core/operations_intelligence/v183_ab_test_runner.py",
    "core/operations_intelligence/v184_continuous_learning_queue.py",
    "core/operations_intelligence/v185_knowledge_freshness_monitor.py",
    "core/operations_intelligence/v186_compliance_checklist.py",
    "core/operations_intelligence/v187_data_retention_manager.py",
    "core/operations_intelligence/v188_secret_rotation_advisor.py",
    "core/operations_intelligence/v189_connector_permission_review.py",
    "core/operations_intelligence/v190_multichannel_output_router.py",
    "core/operations_intelligence/v191_stakeholder_briefing.py",
    "core/operations_intelligence/v192_release_notes_generator.py",
    "core/operations_intelligence/v193_audit_exporter.py",
    "core/operations_intelligence/v194_health_dashboard.py",
    "core/operations_intelligence/v195_executive_summary_packager.py",
    "core/operations_intelligence/v196_operations_intelligence_kernel.py",
    "agent_kernel/operations_intelligence.py",
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
        "V167-V196 OPERATIONS INTELLIGENCE UPGRADE RESULT",
        "=" * 76,
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
        from core.operations_intelligence import init_operations_intelligence, run_operations_intelligence_cycle
        init = init_operations_intelligence(".v167_v196_state")
        lines.append(f"Init operations intelligence: PASS => {init}")

        r = run_operations_intelligence_cycle("继续一次性推进30个大版本，给压缩包和命令", root=".v167_v196_state")
        lines.append(
            f"Cycle: {r.status.value} | completed_versions={r.completed_versions} | "
            f"artifacts={r.artifact_count} | readiness={r.readiness_score} | risk={r.risk_level.value}"
        )
        lines.append(f"Dashboard: {r.dashboard_summary}")
        if r.completed_versions != 30 or r.artifact_count < 25 or r.readiness_score <= 0:
            ok = False
            lines.append("Cycle check: FAIL")
    except Exception as e:
        ok = False
        lines.append("Runtime verification: FAIL")
        lines.append(repr(e))

    lines.append(f"Final cache cleanup: {clean_cache()}")
    lines.append("")
    lines.append("PASS: V167-V196 operations intelligence upgrade applied and verified." if ok else "FAIL: V167-V196 operations intelligence upgrade has blocking issues.")
    RESULT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
