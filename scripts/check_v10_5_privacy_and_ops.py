#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.privacy import PrivacyBoundaryEngine
from infrastructure.ops import OpsHealthSupervisor


def main() -> int:
    privacy = PrivacyBoundaryEngine().prepare_external_payload({"goal": "x", "secret": "abc", "token": "t"}, ["goal", "secret", "token"])
    ops = OpsHealthSupervisor().supervise({"a": 1}, {"a": 1}, [{"name": "api", "status": "blueprint"}])
    result = {
        "status": "pass" if privacy["payload"]["secret"] == "[REDACTED]" and ops["uptime"]["unhealthy_count"] == 0 else "fail",
        "privacy": privacy,
        "ops": ops,
    }
    out = PROJECT_ROOT / "reports" / "V10_5_PRIVACY_AND_OPS_REPORT.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
