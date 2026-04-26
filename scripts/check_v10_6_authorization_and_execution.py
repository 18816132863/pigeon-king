#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.authorization import AuthorizationIntentGateway
from infrastructure.execution_runtime import RealExecutionBroker


def main() -> int:
    action = {"action_id": "send_test", "summary": "send message", "risk_level": "L3", "scopes": ["send"], "side_effect": True}
    auth = AuthorizationIntentGateway().gate(action)
    execution = RealExecutionBroker().prepare(action, auth.get("confirmation_contract"))
    result = {
        "status": "pass" if auth["status"] == "waiting_confirmation" and execution["status"] == "dry_run_only" else "fail",
        "authorization": auth,
        "execution": execution,
        "no_real_side_effect_without_confirmation": execution["real_side_effect"] is False,
    }
    out = PROJECT_ROOT / "reports" / "V10_6_AUTH_EXEC_REPORT.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
