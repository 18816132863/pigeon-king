from __future__ import annotations
from .schemas import ControlArtifact, PlaneStatus, Severity, new_id

class ChangeImpactAnalyzer:
    """V214: change impact analyzer."""
    def analyze(self, changed_modules: list[str], graph_artifact) -> ControlArtifact:
        edges = graph_artifact.payload.get("edges", [])
        impacted = set(changed_modules)
        for e in edges:
            if e["from"] in changed_modules:
                impacted.add(e["to"])
        severity = Severity.HIGH if len(impacted) >= 8 else (Severity.MEDIUM if len(impacted) >= 3 else Severity.LOW)
        status = PlaneStatus.WARN if severity in {Severity.MEDIUM, Severity.HIGH} else PlaneStatus.READY
        return ControlArtifact(new_id("impact"), "change_impact", "impact", status, 0.8, {"changed": changed_modules, "impacted": sorted(impacted), "severity": severity.value})
