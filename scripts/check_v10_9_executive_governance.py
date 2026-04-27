#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.self_governance import ConstitutionalPolicyCore, ValueAlignmentChecker, AutonomyBoundaryManager


def main() -> int:
    rules = ConstitutionalPolicyCore().rules()
    alignment = ValueAlignmentChecker().check({"action": "normal"})
    boundary = AutonomyBoundaryManager().boundary("L3")
    result = {
        "status": "pass" if alignment["status"] == "aligned" and boundary["confirmation_required"] else "fail",
        "rules": rules,
        "alignment": alignment,
        "boundary": boundary,
    }
    out = PROJECT_ROOT / "reports" / "V10_9_EXECUTIVE_GOVERNANCE_REPORT.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
