from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class DecisionMemoBuilder:
    """V174: decision memo builder."""
    def build(self, decision: str, evidence: list[str], risks: list[str]) -> IntelligenceArtifact:
        recommendation = "proceed_with_guardrails" if len(risks) <= 2 else "proceed_after_review"
        return IntelligenceArtifact(new_id("memo"), "decision_memo", "memo", IntelligenceStatus.READY, 0.88, {
            "decision": decision,
            "evidence": evidence,
            "risks": risks,
            "recommendation": recommendation,
        })
