#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import argparse
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from core.self_test import SystemSelfTestAgent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--internal-only", action="store_true")
    args = parser.parse_args()

    result = SystemSelfTestAgent(PROJECT_ROOT).run_extreme_self_test()
    reports = PROJECT_ROOT / "reports"
    reports.mkdir(exist_ok=True)
    out = reports / "V10_EXTREME_SELF_TEST_REPORT.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = reports / "V10_EXTREME_SELF_TEST_REPORT.md"
    md.write_text(
        "# V10 Extreme Self-Test Report\n\n"
        f"- status: {result['status']}\n"
        f"- agent_shape: {result['agent_shape']}\n"
        f"- self_test_shape: {result['self_test_shape']}\n"
        f"- gate_decision: {result['perfection_gate']['decision']}\n"
        f"- gate_score: {result['perfection_gate']['score']}\n"
        f"- blockers: {len(result['perfection_gate']['blockers'])}\n"
        f"- warnings: {len(result['perfection_gate']['warnings'])}\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "status": result["status"],
        "gate_decision": result["perfection_gate"]["decision"],
        "gate_score": result["perfection_gate"]["score"],
        "blockers": len(result["perfection_gate"]["blockers"]),
        "warnings": len(result["perfection_gate"]["warnings"]),
        "report": str(out.relative_to(PROJECT_ROOT)),
    }, ensure_ascii=False, indent=2))
    return 0 if result["perfection_gate"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
