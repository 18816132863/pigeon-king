#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from infrastructure.capability_self_extension import CapabilitySelfExtensionKernel, CapabilityGap


def main() -> int:
    kernel = CapabilitySelfExtensionKernel()
    gap = CapabilityGap("gap_external_research", "missing capability: external research", "solution_search")
    plan = kernel.build_extension_plan(gap, auto_mode=True)
    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    out = reports_dir / "V10_SELF_EXTENSION_REPORT.txt"
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": plan["status"], "candidate_count": len(plan["candidates"]), "sandbox_required": plan["safety_policy"]["sandbox_required"], "report": str(out.relative_to(PROJECT_ROOT))}, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
