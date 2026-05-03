from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, ReportLevel, new_id

class ReportGenerator:
    """V173: structured report generator."""
    def generate(self, title: str, artifacts: list, level: ReportLevel = ReportLevel.OPERATOR) -> IntelligenceArtifact:
        sections = []
        for a in artifacts:
            sections.append({"name": getattr(a, "name", "artifact"), "status": getattr(getattr(a, "status", None), "value", "unknown"), "score": getattr(a, "score", 0)})
        summary = f"{title}: {len(sections)} artifacts, level={level.value}"
        return IntelligenceArtifact(new_id("report"), "operations_report", "report", IntelligenceStatus.READY, 0.9, {"title": title, "level": level.value, "summary": summary, "sections": sections})
