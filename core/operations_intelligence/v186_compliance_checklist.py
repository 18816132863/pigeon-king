from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class ComplianceChecklistEngine:
    """V186: compliance checklist engine."""
    def build(self, domain: str) -> IntelligenceArtifact:
        base = ["no_false_claims", "source_traceability", "approval_for_external_side_effects"]
        if domain in {"food", "ecommerce"}:
            base += ["ordinary_food_vs_health_food_boundary", "no_medical_claims", "license_and_sc_docs_required"]
        if domain in {"software", "agent"}:
            base += ["secret_redaction", "rollback_plan", "sandbox_for_extensions"]
        return IntelligenceArtifact(new_id("compliance"), "compliance_checklist", "compliance", IntelligenceStatus.READY, 0.9, {"domain": domain, "checklist": base})
