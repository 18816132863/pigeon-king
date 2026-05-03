from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, Severity, new_id

class PostmortemGenerator:
    """V222: postmortem generator."""
    def generate(self, incident: str, severity: Severity, root_causes: list[str]) -> ControlArtifact:
        payload = {
            "incident": incident,
            "severity": severity.value,
            "root_causes": root_causes,
            "actions": ["prevent recurrence", "add regression", "update playbook"],
        }
        return ControlArtifact(new_id("postmortem"), "postmortem", "postmortem", PlaneStatus.READY, 0.85, payload)
