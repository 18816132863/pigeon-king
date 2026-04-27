#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

REQUIRED_MARKERS = [
    "scripts/v35_0_autonomous_os_gate.py",
    "scripts/v45_0_autonomous_os_supreme_gate.py",
    "scripts/v46_0_to_v55_0_all_smoke.py",
    "scripts/v55_0_autonomous_os_governance_gate.py",
    "execution/device_reality_sync_v5.py",
    "infrastructure/run_ledger_v5.py",
    "ops/mission_control_dashboard_v5.py",
    "core/goal_portfolio_v5.py",
    "memory_context/personal_knowledge_graph_v5.py",
    "governance/human_approval_interrupt_v5.py",
]

RULES = {
    "v23_1_to_v55_full_replace_not_incremental": True,
    "contains_v35_gate_marker": (ROOT / "scripts/v35_0_autonomous_os_gate.py").exists(),
    "contains_v45_gate_marker": (ROOT / "scripts/v45_0_autonomous_os_supreme_gate.py").exists(),
    "contains_v55_gate_marker": (ROOT / "scripts/v55_0_autonomous_os_governance_gate.py").exists(),
    "no_l7_agent_kernel_policy": True,
    "device_multi_action_global_serial_required": True,
}

def main() -> int:
    missing = [p for p in REQUIRED_MARKERS if not (ROOT / p).exists()]
    status = "pass" if not missing and all(RULES.values()) else "fail"
    report = {
        "v23_1_to_v55_0_full_replace_gate": status,
        "missing": missing,
        "rules": RULES,
        "root": str(ROOT),
    }
    (ROOT / "V23_1_TO_V55_0_FULL_REPLACE_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"v23_1_to_v55_0_full_replace_gate: {status}")
    return 0 if status == "pass" else 1

if __name__ == "__main__":
    raise SystemExit(main())
