from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, new_id

class WorkflowTemplateRegistry:
    """V234: workflow template registry."""
    def list_templates(self) -> FabricArtifact:
        templates = {
            "upgrade_release": ["build_patch", "apply", "verify", "report"],
            "high_risk_action": ["dry_run", "approval", "execute_guarded", "audit"],
            "incident_response": ["freeze", "diagnose", "rollback", "postmortem"],
        }
        return FabricArtifact(new_id("workflow"), "workflow_templates", "workflow", FabricStatus.READY, 0.91, {"templates": templates})
