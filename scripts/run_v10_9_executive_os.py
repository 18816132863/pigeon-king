#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from orchestration.executive_personal_os_orchestrator import ExecutivePersonalOSOrchestrator


def main() -> int:
    result = ExecutivePersonalOSOrchestrator().run(
        "一句话完成我想做的事，没技能自己找方案，真实执行前必须确认，最后给我完整结果",
        {"signals": [{"text": "直接给我完整包"}], "risk_level": "L2"},
    )
    out = PROJECT_ROOT / "reports" / "V10_9_EXECUTIVE_PERSONAL_OS_REPORT.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "shape": result["shape"],
        "maturity": result["executive"]["maturity"]["score"],
        "can_claim_done": result["can_claim_done"],
        "report": str(out.relative_to(PROJECT_ROOT)),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
