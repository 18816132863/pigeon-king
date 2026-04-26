#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from orchestration.strategic_personal_os_orchestrator import StrategicPersonalOSOrchestrator


def main() -> int:
    goal = "一句话完成目标，能接外部能力，越用越像我，不要猜，给我完整结果"
    result = StrategicPersonalOSOrchestrator().run(goal, {"events": [{"status": "ok"}]})
    out = PROJECT_ROOT / "reports" / "V10_4_STRATEGIC_PERSONAL_OS_REPORT.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "shape": result["shape"],
        "readiness": result["readiness"]["status"],
        "connector_blueprints": len(result["connector_blueprints"]),
        "report": str(out.relative_to(PROJECT_ROOT)),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
