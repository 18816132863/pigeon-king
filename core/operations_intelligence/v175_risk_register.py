from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, RiskLevel, new_id

class RiskRegister:
    """V175: operational risk register."""
    def register(self, goal: str, signals: list[str]) -> IntelligenceArtifact:
        risks = []
        if any(x in goal for x in ["发送", "安装", "删除", "转账", "token", "密钥"]):
            risks.append({"name": "side_effect_or_sensitive_action", "level": RiskLevel.HIGH.value, "mitigation": "approval + dry-run + evidence"})
        if "大版本" in goal or "30" in goal:
            risks.append({"name": "large_batch_change", "level": RiskLevel.MEDIUM.value, "mitigation": "verification script + rollback notes"})
        if "cost" in signals:
            risks.append({"name": "budget_drift", "level": RiskLevel.MEDIUM.value, "mitigation": "budget governor"})
        level = RiskLevel.HIGH if any(r["level"] == RiskLevel.HIGH.value for r in risks) else (RiskLevel.MEDIUM if risks else RiskLevel.LOW)
        return IntelligenceArtifact(new_id("risk"), "risk_register", "risk", IntelligenceStatus.READY, 0.86, {"risk_level": level.value, "risks": risks})
