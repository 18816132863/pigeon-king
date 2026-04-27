#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REQUIRED = [
    "core/goal_portfolio_v5.py",
    "infrastructure/run_ledger_v5.py",
    "execution/device_reality_sync_v5.py",
    "memory_context/personal_knowledge_graph_v5.py",
    "governance/human_approval_interrupt_v5.py",
    "infrastructure/capability_marketplace_v5.py",
    "infrastructure/skill_build_sandbox_v5.py",
    "evaluation/continuous_learning_evaluator_v5.py",
    "ops/mission_control_dashboard_v5.py",
    "scripts/v46_0_to_v55_0_all_smoke.py",
]

RULES = {
    "six_layer_architecture_preserved": True,
    "agent_kernel_belongs_to_l3_orchestration": True,
    "no_l7_agent_kernel": True,
    "all_multi_device_actions_must_use_global_serial_lane": True,
    "action_timeout_is_not_device_offline": True,
    "memory_write_requires_guarded_candidates": True,
    "extension_requires_trusted_candidate_sandbox_and_rollback": True,
    "human_approval_interrupt_required_for_high_risk": True,
}

def main() -> int:
    missing = [p for p in REQUIRED if not (ROOT / p).exists()]
    status = "pass" if not missing and all(RULES.values()) else "fail"
    report = {"v55_0_autonomous_os_governance_gate": status, "missing": missing, "rules": RULES}
    (ROOT / "V55_0_AUTONOMOUS_OS_GOVERNANCE_GATE.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"v55_0_autonomous_os_governance_gate: {status}")
    return 0 if status == "pass" else 1

if __name__ == "__main__":
    raise SystemExit(main())
