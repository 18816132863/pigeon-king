from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class StakeholderBriefingGenerator:
    """V191: stakeholder briefing generator."""
    def generate(self, stakeholder: str, highlights: list[str]) -> IntelligenceArtifact:
        brief = {
            "stakeholder": stakeholder,
            "headline": highlights[0] if highlights else "阶段完成",
            "bullets": highlights[:6],
            "ask": "执行覆盖命令并反馈验收结果" if stakeholder in {"大龙虾", "technical_executor"} else "确认下一步方向",
        }
        return IntelligenceArtifact(new_id("brief"), "stakeholder_briefing", "briefing", IntelligenceStatus.READY, 0.9, brief)
