from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class ExecutiveSummaryPackager:
    """V195: executive summary packager."""
    def package(self, title: str, dashboard_summary: str, top_actions: list[str]) -> IntelligenceArtifact:
        payload = {
            "title": title,
            "dashboard_summary": dashboard_summary,
            "top_actions": top_actions[:5],
            "decision": "continue" if "blocked" not in dashboard_summary else "fix_blockers_first",
        }
        score = 0.9 if payload["decision"] == "continue" else 0.65
        status = IntelligenceStatus.READY if score >= 0.75 else IntelligenceStatus.WARN
        return IntelligenceArtifact(new_id("execsum"), "executive_summary_package", "executive_summary", status, score, payload)
