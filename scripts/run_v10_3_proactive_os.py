#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from orchestration.proactive_personal_os_orchestrator import ProactivePersonalOSOrchestrator


def main() -> int:
    goal = "一句话帮我完成目标，没技能就自己找方案，能接外部能力但必须安全"
    result = ProactivePersonalOSOrchestrator().run(goal, {"signals": [{"priority": "high", "type": "goal"}]})
    out = PROJECT_ROOT / "reports" / "V10_3_PROACTIVE_PERSONAL_OS_REPORT.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "shape": result["shape"],
        "capability_discovery": bool(result["capability_discovery"]),
        "execution_allowed_now": result["execution_allowed_now"],
        "report": str(out.relative_to(PROJECT_ROOT)),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
