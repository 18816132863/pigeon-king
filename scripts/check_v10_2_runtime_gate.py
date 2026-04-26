#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.runtime import AutonomousRuntimeKernel
from governance.policy import RuntimePolicyEnforcer


def main() -> int:
    plan = AutonomousRuntimeKernel().process("自动安装外部能力")
    gate = RuntimePolicyEnforcer().enforce(plan)
    out = {
        "status": "pass" if gate["status"] == "requires_confirmation" else "fail",
        "gate": gate,
        "risk_level": plan["decision_cycle"]["risk_level"],
        "strong_confirmation_enforced": gate["status"] == "requires_confirmation",
    }
    report = PROJECT_ROOT / "reports" / "V10_2_RUNTIME_GATE_REPORT.json"
    report.parent.mkdir(exist_ok=True)
    report.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
