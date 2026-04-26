#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from infrastructure.capability_acquisition import SkillDiscoveryEngine, SandboxPromotionGate
from core.verification import RollbackManager, AuditTrail


def main() -> int:
    discovered = SkillDiscoveryEngine().discover("missing_external_capability")
    gate = SandboxPromotionGate().evaluate(
        {"success": True},
        AuditTrail().build_event("test", {}),
        RollbackManager().build_rollback_plan([{"step": "x"}]),
    )
    result = {
        "status": "pass" if discovered["candidates"] and gate["status"] == "promote_to_experimental" else "fail",
        "candidate_count": len(discovered["candidates"]),
        "gate": gate,
        "direct_install_allowed": any(c["policy"]["direct_install_allowed"] for c in discovered["candidates"]),
    }
    out = PROJECT_ROOT / "reports" / "V10_3_CAPABILITY_ACQUISITION_REPORT.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "pass" and result["direct_install_allowed"] is False else 1


if __name__ == "__main__":
    raise SystemExit(main())
