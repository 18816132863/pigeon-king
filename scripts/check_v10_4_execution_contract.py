#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.execution_contract import ExecutionContract, ExecutionReadinessGate


def main() -> int:
    contract = ExecutionContract().build({"mission_id": "test"}, "L3")
    readiness = ExecutionReadinessGate().check(contract)
    result = {
        "status": "pass" if readiness["status"] == "waiting_confirmation" else "fail",
        "contract": contract,
        "readiness": readiness,
        "strong_confirmation_enforced": readiness["status"] == "waiting_confirmation",
    }
    out = PROJECT_ROOT / "reports" / "V10_4_EXECUTION_CONTRACT_REPORT.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
