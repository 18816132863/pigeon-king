#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from orchestration.reality_connected_personal_os_orchestrator import RealityConnectedPersonalOSOrchestrator


def main() -> int:
    result = RealityConnectedPersonalOSOrchestrator().run(
        "接入真实外部能力但必须先授权、可审计、可回滚",
        {
            "facts": [{"name": "user_requested", "value": True}],
            "connectors": [{"connector_id": "api", "status": "planned"}],
            "device_runtime": {"adapter_loaded": False},
            "scopes": ["read", "search", "install"],
        },
    )
    out = PROJECT_ROOT / "reports" / "V10_6_REALITY_CONNECTED_OS_REPORT.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "shape": result["shape"],
        "authorization_status": result["authorization"]["status"],
        "real_execution_allowed_now": result["real_execution_allowed_now"],
        "report": str(out.relative_to(PROJECT_ROOT)),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
