#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from orchestration.continuous_personal_os_orchestrator import ContinuousPersonalOSOrchestrator


def main() -> int:
    result = ContinuousPersonalOSOrchestrator().run(
        "长期持续推进系统，自己关注重点，自己模拟方案，保护隐私，越用越像我",
        {
            "signals": [{"priority": "high", "type": "goal", "reason": "user_requested_fast_iteration"}],
            "sources": [{"type": "internal_report", "topic": "架构"}],
            "payload": {"goal": "continue", "secret": "should_not_leave"},
        },
    )
    out = PROJECT_ROOT / "reports" / "V10_5_CONTINUOUS_PERSONAL_OS_REPORT.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "shape": result["shape"],
        "initiative_count": len(result["continuous_tick"]["initiatives"]["initiatives"]),
        "execution_side_effect": result["execution_side_effect"],
        "report": str(out.relative_to(PROJECT_ROOT)),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
