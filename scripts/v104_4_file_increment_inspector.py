#!/usr/bin/env python3
"""
V104.4: 文件增量发现 + 架构覆盖巡检。

功能：
1. 建立文件基线（首次运行）
2. 后续运行时自动检测新增/删除/变更的文件
3. 检查新增文件是否已纳入架构文档（通过 doc_fusion_engine）
4. 输出报告到 reports/inventory/

使用方式：
  python3 scripts/v104_4_file_increment_inspector.py

输出：
  reports/inventory/file_baseline_snapshot.json      # 基线快照
  reports/inventory/file_increment_report.json        # 增量报告
"""
from __future__ import annotations
import hashlib, json, re, sys
from datetime import datetime
from pathlib import Path

ROOT = Path.cwd()
INVENTORY_DIR = ROOT / "reports" / "inventory"
INVENTORY_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOT_FILE = INVENTORY_DIR / "file_baseline_snapshot.json"
INCREMENT_FILE = INVENTORY_DIR / "file_increment_report.json"

# 排除的目录名/模式（部分匹配）
EXCLUDE_PATTERNS = {
    "__pycache__", ".pytest_cache", "node_modules",
    ".backup_", ".repair_state", "v86_backup_",
    ".v104_", ".v98_",
    "archive", "releases", "generated-images",
}
# 扩展名排除
EXCLUDE_EXTS = {".pyc", ".zip", ".tar.gz", ".gz", ".7z", ".rar", ".egg-info"}
# 顶层目录硬排除
EXCLUDE_TOP = {".openclaw", ".git", "__pycache__", "node_modules", "repo"}

LAYER_MAP = {
    "core/": "L1-Core",
    "memory_context/": "L2-Memory",
    "orchestration/": "L3-Orchestration",
    "execution/": "L4-Execution",
    "governance/": "L5-Governance",
    "infrastructure/": "L6-Infrastructure",
    "scripts/": "scripts",
    "docs/": "docs",
    "tests/": "tests",
    "skills/": "skills",
    "config/": "config",
    "data/": "data",
}

# 已纳入架构文档的核心模块清单
KNOW_ARCH_FILES = {
    "infrastructure/mainline_hook.py",
    "infrastructure/offline_runtime_guard.py",
    "infrastructure/skill_policy_gate.py",
    "infrastructure/architecture_inspector.py",
    "orchestration/runtime_bus.py",
    "orchestration/single_runtime_entrypoint.py",
    "governance/runtime_commit_barrier_bridge.py",
    "governance/v90_final_access_gateway.py",
    "governance/constitutional_runtime/operating_constitution.py",
    "governance/constitutional_runtime/preflight_gate.py",
    "governance/constitutional_runtime/risk_proof.py",
    "governance/embodied_pending_state/commit_barrier.py",
    "governance/embodied_pending_state/action_semantics.py",
    "governance/embodied_pending_state/freeze_switch.py",
    "governance/embodied_pending_state/readiness_gate.py",
    "governance/embodied_pending_state/maturity_scorecard.py",
    "governance/evolution_safety/autonomy_policy.py",
    "governance/evolution_safety/memory_governance.py",
    "governance/evolution_safety/persona_memory_audit.py",
    "governance/red_team_safety/circuit_breakers.py",
    "governance/red_team_safety/red_team_suite.py",
    "governance/red_team_safety/release_assurance.py",
    "governance/safety_governor/approval_gate.py",
    "governance/safety_governor/runtime_gate.py",
    "governance/safety_governor/policy_engine.py",
    "governance/safety_governor/risk_levels.py",
    "governance/safety_governor/game_policy.py",
    "governance/persona/humanlike_behavior_policy.py",
    "governance/context/anti_context_amnesia_guard.py",
    "governance/access_control/access_control.py",
    "governance/access_control/permission_lease.py",
    "governance/codex/judgement_engine.py",
    "governance/codex/personal_codex.py",
    "governance/constitutional_judge_v4.py",
    "governance/audit/execution_audit_ledger.py",
    "governance/audit/explainer.py",
    "governance/audit/feedback.py",
    "governance/audit/summarizer.py",
    "governance/human_approval_interrupt_v5.py",
    "governance/policy/adaptive_execution_policy.py",
    "governance/policy/autonomy_level_policy.py",
    "governance/policy/autonomy_safety_case_v6.py",
    "governance/policy/connector_governance_broker_v7.py",
    "governance/policy/device_action_contract_policy.py",
    "governance/policy/end_side_global_serial_policy.py",
    "governance/policy/execution_autopilot.py",
    "governance/policy/failure_taxonomy.py",
    "governance/policy/organ_conflict_policy.py",
    "governance/policy/risk_tier_matrix.py",
    "governance/policy/runtime_policy_enforcer.py",
    "governance/evaluation/autonomy_regression_matrix_v4.py",
    "governance/evaluation/continuous_learning_evaluator_v5.py",
    "governance/security/security_confirmation.py",
    "governance/security/strong_confirmation.py",
    "governance/scheduler/realtime_scheduler.py",
    "governance/self_audit/audit_verifier.py",
    "governance/ops/autonomous_os_mission_control_v4.py",
    "governance/ops/mission_control_dashboard_v5.py",
    "memory_context/persona/persona_state_machine.py",
    "memory_context/persona/relationship_memory.py",
    "memory_context/persona/continuity_summary.py",
    "memory_context/persona/persona_voice_renderer.py",
    "memory_context/persona/persona_voice_stabilizer.py",
    "memory_context/persona/persona_consistency_checker.py",
    "memory_context/persona/emotion_tagged_memory.py",
    "memory_context/persona/self_reflection_log.py",
    "memory_context/context/context_capsule.py",
    "memory_context/context/session_handoff.py",
    "memory_context/context/memory_recall_bootstrap.py",
    "memory_context/context/context_priority_router.py",
    "memory_context/vector/embedding.py",
    "memory_context/vector/qdrant_store.py",
    "memory_context/vector/cache.py",
    "memory_context/vector/history.py",
    "memory_context/knowledge_graph_bridge.py",
    "memory_context/personal_knowledge_graph_v5.py",
    "memory_context/personal_memory_kernel_v4.py",
    "memory_context/personal_memory_lifecycle_v6.py",
    "memory_context/memory_writeback_guard_v2.py",
    "memory_context/preference_evolution_model_v7.py",
    "memory_context/preference_evolution_bridge.py",
    "memory_context/cross_lingual/cross_lingual.py",
    "memory_context/multimodal/multimodal_search.py",
    "memory_context/maintenance/check_coverage.py",
    "memory_context/maintenance/rebuild_fts.py",
    "memory_context/maintenance/run_maintenance.py",
    "memory_context/maintenance/vector_system_optimizer.py",
    "memory_context/personalization/personalization_engine.py",
    "memory_context/coverage/vector_coverage_monitor.py",
    "memory_context/learning_loop/execution_memory.py",
    "memory_context/learning_loop/pattern_extractor.py",
    "memory_context/learning_loop/preference_profile.py",
    "memory_context/learning_loop/success_path_store.py",
    "memory_context/learning_loop/plan_optimizer.py",
    "memory_context/learning_loop/audit_replay/audit_replay_learner.py",
    "memory_context/learning_loop/audit_replay/decision_trace_index.py",
    "memory_context/learning_loop/audit_replay/mistake_prevention_rules.py",
    "memory_context/learning_loop/identity_evolution/correction_incorporator.py",
    "memory_context/learning_loop/identity_evolution/identity_evolution_engine.py",
    "memory_context/learning_loop/identity_evolution/preference_versioning.py",
    "memory_context/learning_loop/meta_learning/evaluation_memory.py",
    "memory_context/learning_loop/meta_learning/meta_learning_engine.py",
    "memory_context/learning_loop/meta_learning/prompt_strategy_optimizer.py",
    "memory_context/learning_loop/personal_evolution/behavior_pattern_miner.py",
    "memory_context/learning_loop/personal_evolution/personal_feedback_router.py",
    "memory_context/learning_loop/personal_evolution/risk_tolerance_calibrator.py",
    "memory_context/learning_loop/personal_model/decision_style_model.py",
    "memory_context/learning_loop/personal_model/preference_evolution.py",
    "memory_context/learning_loop/reflection/failure_pattern_analyzer.py",
    "memory_context/learning_loop/reflection/reflection_engine.py",
    "memory_context/learning_loop/reflection/success_pattern_promoter.py",
    "scripts/v102_persona_continuity_gate.py",
    "scripts/v103_context_reload_persona_consistency_gate.py",
    "scripts/v103_1_persona_truth_cleanup_gate.py",
    "scripts/v104_final_consistency_conflict_cleanup_gate.py",
    "scripts/v104_1_final_consistency_enforcement_gate.py",
    "scripts/v104_2_runtime_hardening_apply.py",
    "scripts/v104_2_runtime_hardening_gate.py",
    "scripts/v104_3_runtime_fusion_coordination_apply.py",
    "scripts/v104_3_runtime_fusion_coordination_gate.py",
    "scripts/v104_4_file_increment_inspector.py",
    "scripts/doc_fusion_engine.py",
    "scripts/unified_inspector_v10.py",
    "scripts/unified_inspector_v11.py",
    "scripts/run_release_gate.py",
    "scripts/dedicated_skill_paths_check.py",
    "scripts/skill_connectivity_gate.py",
    "scripts/cleanup_orphan_skills.py",
    "scripts/v100_final_pending_access_release_gate.py",
    "scripts/v100_packaging_integrity_gate.py",
    "docs/ARCHITECTURE_V10.md",
    "docs/CHANGELOG.md",
    "docs/ARCHITECTURE_RELATIONSHIP.md",
    "docs/QUICKSTART.md",
    "docs/DEPLOY.md",
    "docs/CONTRIBUTING.md",
    "docs/README.md",
    "docs/OFFLINE_RUNTIME_GUARD.md",
    "docs/V104_README.md",
    "docs/V7.2.0_ARCHITECTURE.md",
    "docs/V7.2.0_UNIFIED_ARCHITECTURE.md",
}


def should_exclude(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    parts = rel.parts
    # 顶层排除
    for part in parts[:1]:
        if part in EXCLUDE_TOP:
            return True
    # 路径段排除
    for part in parts:
        for pattern in EXCLUDE_PATTERNS:
            if pattern in part:
                return True
    # 扩展名排除
    if rel.suffix in EXCLUDE_EXTS:
        return True
    return False


def classify_layer(path: str) -> str:
    for prefix, layer in sorted(LAYER_MAP.items(), key=lambda x: -len(x[0])):
        if path.startswith(prefix):
            return layer
    return "unknown"


def discover_all() -> list[dict]:
    files = []
    for f in sorted(ROOT.rglob("*")):
        if not f.is_file():
            continue
        try:
            rel = f.relative_to(ROOT)
        except ValueError:
            continue
        if should_exclude(f):
            continue
        if not f.name.endswith(".py") and not f.suffix:
            continue  # skip files without extension unless .py
        # count only .py and .md for baseline; but track size for all
        if f.suffix not in (".py", ".md"):
            continue
        files.append({
            "path": str(rel),
            "size": f.stat().st_size,
            "mtime": f.stat().st_mtime,
            "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
            "layer": classify_layer(str(rel)),
        })
    return files


def load_snapshot() -> list[dict]:
    if SNAPSHOT_FILE.exists():
        try:
            data = json.loads(SNAPSHOT_FILE.read_text(encoding="utf-8"))
            return data.get("files", [])
        except Exception:
            pass
    return []


def save_snapshot(files: list[dict]):
    SNAPSHOT_FILE.write_text(json.dumps({
        "version": 1,
        "generated_at": datetime.now().isoformat(),
        "file_count": len(files),
        "files": files,
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def compute_delta(current: list[dict], baseline: list[dict]) -> dict:
    cur_map = {f["path"]: f for f in current}
    base_map = {f["path"]: f for f in baseline}
    cur_set = set(cur_map.keys())
    base_set = set(base_map.keys())

    added_paths = sorted(cur_set - base_set)
    removed_paths = sorted(base_set - cur_set)
    changed = []

    for path in cur_set & base_set:
        cf = cur_map[path]
        bf = base_map[path]
        if cf["sha256"] != bf["sha256"] or cf["size"] != bf["size"]:
            changed.append({
                "path": path,
                "old_size": bf["size"],
                "new_size": cf["size"],
                "layer": cf["layer"],
            })

    return {
        "added": [{"path": p, "layer": cur_map[p]["layer"]} for p in added_paths],
        "removed": [{"path": p, "layer": base_map[p]["layer"]} for p in removed_paths],
        "changed": changed,
        "total_added": len(added_paths),
        "total_removed": len(removed_paths),
        "total_changed": len(changed),
    }


def check_arch_coverage(files: list[dict]) -> dict:
    total = len(files)
    known = sum(1 for f in files if f["path"] in KNOW_ARCH_FILES)

    # 6层核心文件未归档
    core_not_in_arch = []
    for f in files:
        layer = f["layer"]
        if layer and layer.startswith("L") and layer.count("-") == 1:
            if f["path"] not in KNOW_ARCH_FILES:
                core_not_in_arch.append(f["path"])

    return {
        "total_files": total,
        "in_arch_doc": known,
        "not_in_arch_doc": len(core_not_in_arch),
        "candidates_for_arch_fusion": core_not_in_arch[:20],
        "note": f"{known}/{total} 已纳入架构文档; {len(core_not_in_arch)} 个六层核心文件未纳入",
    }


def run() -> dict:
    current = discover_all()
    baseline = load_snapshot()

    is_first = len(baseline) == 0

    if is_first:
        delta = {"added": [], "removed": [], "changed": [],
                 "total_added": 0, "total_removed": 0, "total_changed": 0,
                 "note": "首次运行，基线已建立"}
    else:
        delta = compute_delta(current, baseline)

    coverage = check_arch_coverage(current)
    save_snapshot(current)

    report = {
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "baseline_file_count": len(baseline),
        "current_file_count": len(current),
        "is_first_run": is_first,
        "delta": delta,
        "arch_coverage": coverage,
    }

    INCREMENT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # Print summary
    print(f"📦 文件总数: {len(current)}")
    if is_first:
        print("📌 首次运行，基线已建立")
        print(f"  基线保存至: {SNAPSHOT_FILE}")
    else:
        d = delta
        print(f"➕ 新增: {d['total_added']}")
        if d['total_added'] > 0:
            for a in d['added']:
                print(f"     {a['path']} ({a['layer']})")
        print(f"➖ 删除: {d['total_removed']}")
        print(f"✏️ 变更: {d['total_changed']}")
    print(f"📋 架构覆盖: {coverage['in_arch_doc']}/{coverage['total_files']} 已归档")
    if coverage['not_in_arch_doc'] > 0:
        print(f"⚠️ {coverage['not_in_arch_doc']} 个核心文件未在架构文档中")
        print(f"   建议运行 doc_fusion_engine 融合")
    print(f"📊 报告: {INCREMENT_FILE}")

    return report


if __name__ == "__main__":
    run()
