#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from orchestration.personal_autonomous_os_agent import PersonalAutonomousOSAgent


def main() -> int:
    agent = PersonalAutonomousOSAgent()
    sample_goal = "一句话帮我自动规划任务，缺技能就自己查找方案并在安全边界内补能力"
    result = agent.process_goal(sample_goal, {"autonomy_level": "bounded_high"})
    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    out = reports_dir / "V10_AUTONOMOUS_AGENT_REPORT.txt"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "agent_shape": result["agent_shape"],
        "next_action": result["next_action"],
        "gap_count": len(result["capability_gaps"]),
        "report": str(out.relative_to(PROJECT_ROOT)),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
