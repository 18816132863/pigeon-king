"""V54.0 Mission Control Dashboard V5.

Aggregates goal, workflow, device lane, approval, memory and extension signals into
one report for operators and release gates.
"""
from __future__ import annotations
from typing import Any, Dict
from datetime import datetime, timezone

class MissionControlDashboardV5:
    def build_report(self, sections: Dict[str, Any]) -> Dict[str, Any]:
        required = ["goal", "workflow", "device_lane", "governance", "memory", "extension"]
        missing = [k for k in required if k not in sections]
        status = "pass" if not missing and all(sections.get(k, {}).get("status", "pass") != "fail" for k in required) else "review"
        return {
            "version": "v54.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "missing_sections": missing,
            "sections": sections,
        }
