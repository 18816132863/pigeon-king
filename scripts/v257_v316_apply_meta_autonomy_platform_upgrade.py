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
RESULT = ROOT / "V257_V316_META_AUTONOMY_PLATFORM_UPGRADE_RESULT.txt"

REQUIRED = ['core/meta_autonomy_platform/__init__.py', 'core/meta_autonomy_platform/schemas.py', 'core/meta_autonomy_platform/v316_meta_autonomy_platform_kernel.py', 'agent_kernel/meta_autonomy_platform.py', 'core/meta_autonomy_platform/v257_capability_marketplace.py', 'core/meta_autonomy_platform/v258_skill_composer.py', 'core/meta_autonomy_platform/v259_workflow_compiler.py', 'core/meta_autonomy_platform/v260_decision_graph_optimizer.py', 'core/meta_autonomy_platform/v261_intent_cache.py', 'core/meta_autonomy_platform/v262_semantic_router.py', 'core/meta_autonomy_platform/v263_task_batcher.py', 'core/meta_autonomy_platform/v264_priority_queue_planner.py', 'core/meta_autonomy_platform/v265_parallel_plan_simulator.py', 'core/meta_autonomy_platform/v266_state_consistency_checker.py', 'core/meta_autonomy_platform/v267_isolation_boundary_checker.py', 'core/meta_autonomy_platform/v268_policy_diff_engine.py', 'core/meta_autonomy_platform/v269_approval_sla_planner.py', 'core/meta_autonomy_platform/v270_credential_hygiene_scanner.py', 'core/meta_autonomy_platform/v271_prompt_firewall.py', 'core/meta_autonomy_platform/v272_tool_allowlist_compiler.py', 'core/meta_autonomy_platform/v273_data_minimization_engine.py', 'core/meta_autonomy_platform/v274_context_deduplicator.py', 'core/meta_autonomy_platform/v275_memory_conflict_resolver.py', 'core/meta_autonomy_platform/v276_knowledge_graph_index.py', 'core/meta_autonomy_platform/v277_ontology_mapper.py', 'core/meta_autonomy_platform/v278_retrieval_strategy_tuner.py', 'core/meta_autonomy_platform/v279_source_credibility_scorer.py', 'core/meta_autonomy_platform/v280_evidence_linker.py', 'core/meta_autonomy_platform/v281_artifact_dependency_packager.py', 'core/meta_autonomy_platform/v282_patch_conflict_resolver.py', 'core/meta_autonomy_platform/v283_schema_evolution_planner.py', 'core/meta_autonomy_platform/v284_migration_dry_run_engine.py', 'core/meta_autonomy_platform/v285_compatibility_matrix_builder.py', 'core/meta_autonomy_platform/v286_device_capability_matcher.py', 'core/meta_autonomy_platform/v287_local_executor_planner.py', 'core/meta_autonomy_platform/v288_remote_executor_planner.py', 'core/meta_autonomy_platform/v289_sandbox_fleet_manager.py', 'core/meta_autonomy_platform/v290_runtime_contract_broker.py', 'core/meta_autonomy_platform/v291_operation_idempotency_guard.py', 'core/meta_autonomy_platform/v292_side_effect_reconciliation.py', 'core/meta_autonomy_platform/v293_human_checkpoint_orchestrator.py', 'core/meta_autonomy_platform/v294_audit_trail_compressor.py', 'core/meta_autonomy_platform/v295_observability_correlation_engine.py', 'core/meta_autonomy_platform/v296_token_budget_allocator.py', 'core/meta_autonomy_platform/v297_cost_center_allocator.py', 'core/meta_autonomy_platform/v298_latency_budget_planner.py', 'core/meta_autonomy_platform/v299_throughput_controller.py', 'core/meta_autonomy_platform/v300_concurrency_governor.py', 'core/meta_autonomy_platform/v301_adaptive_rate_limiter.py', 'core/meta_autonomy_platform/v302_load_shedding_controller.py', 'core/meta_autonomy_platform/v303_regression_risk_predictor.py', 'core/meta_autonomy_platform/v304_quality_drift_detector.py', 'core/meta_autonomy_platform/v305_agent_maturity_assessor.py', 'core/meta_autonomy_platform/v306_roadmap_reprioritizer.py', 'core/meta_autonomy_platform/v307_technical_debt_register.py', 'core/meta_autonomy_platform/v308_deprecation_manager.py', 'core/meta_autonomy_platform/v309_user_journey_tracer.py', 'core/meta_autonomy_platform/v310_stakeholder_alignment_matrix.py', 'core/meta_autonomy_platform/v311_operator_training_packager.py', 'core/meta_autonomy_platform/v312_runbook_quality_scorer.py', 'core/meta_autonomy_platform/v313_model_quality_arbiter.py', 'core/meta_autonomy_platform/v314_vendor_governance_registry.py', 'core/meta_autonomy_platform/v315_platform_certification_board.py']

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
        "V257-V316 META AUTONOMY PLATFORM UPGRADE RESULT",
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
        from core.meta_autonomy_platform import init_meta_autonomy_platform, run_meta_autonomy_platform_cycle
        init = init_meta_autonomy_platform(".v257_v316_state")
        lines.append(f"Init meta autonomy platform: PASS => {init}")

        r = run_meta_autonomy_platform_cycle("继续一次性多推进功能，推进60个版本，给压缩包和命令", root=".v257_v316_state")
        lines.append(
            f"Cycle: {r.status.value} | completed_versions={r.completed_versions} | "
            f"artifacts={r.artifact_count} | readiness={r.readiness_score} | gate={r.gate.value}"
        )
        lines.append(f"Dashboard: {r.dashboard_summary}")
        if r.completed_versions != 60 or r.artifact_count < 60 or r.readiness_score <= 0:
            ok = False
            lines.append("Cycle check: FAIL")
    except Exception as e:
        ok = False
        lines.append("Runtime verification: FAIL")
        lines.append(repr(e))

    lines.append(f"Final cache cleanup: {clean_cache()}")
    lines.append("")
    lines.append("PASS: V257-V316 meta autonomy platform upgrade applied and verified." if ok else "FAIL: V257-V316 meta autonomy platform upgrade has blocking issues.")
    RESULT.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines), flush=True)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
