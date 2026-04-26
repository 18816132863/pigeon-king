#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from orchestration.autonomous_runtime_orchestrator import AutonomousRuntimeOrchestrator


def main() -> int:
    goal = "一句话帮我完成目标，如果没技能就自己找方案并生成安全扩展计划"
    result = AutonomousRuntimeOrchestrator().run_goal(goal, {"autonomy_level": "bounded_high"})
    out = PROJECT_ROOT / "reports" / "V10_2_AUTONOMOUS_RUNTIME_REPORT.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "shape": result["orchestrator_shape"],
        "policy": result["policy_result"]["status"],
        "acquisition_plans": len(result["acquisition_plans"]),
        "report": str(out.relative_to(PROJECT_ROOT)),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
