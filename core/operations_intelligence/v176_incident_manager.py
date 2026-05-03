from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, PriorityLevel, new_id

class IncidentManager:
    """V176: incident classification and response plan."""
    def classify(self, symptoms: list[str]) -> IntelligenceArtifact:
        critical = any(x in " ".join(symptoms).lower() for x in ["data_loss", "secret", "payment", "delete"])
        priority = PriorityLevel.P0 if critical else (PriorityLevel.P1 if symptoms else PriorityLevel.P3)
        response = ["freeze side effects", "capture evidence", "rollback if needed", "write incident report"] if critical else ["diagnose", "retry safely", "record outcome"]
        return IntelligenceArtifact(new_id("incident"), "incident_plan", "incident", IntelligenceStatus.READY, 0.87, {"priority": priority.value, "symptoms": symptoms, "response": response})
