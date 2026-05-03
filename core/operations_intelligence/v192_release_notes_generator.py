from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class ReleaseNotesGenerator:
    """V192: release notes generator."""
    def generate(self, version_from: str, version_to: str, features: list[str]) -> IntelligenceArtifact:
        notes = {
            "range": f"{version_from}-{version_to}",
            "added": features,
            "verification": f"run scripts/{version_from.lower()}_{version_to.lower()}_verify.py if present",
            "rollback": "restore previous workspace snapshot if verification fails",
        }
        return IntelligenceArtifact(new_id("notes"), "release_notes", "release_notes", IntelligenceStatus.READY, 0.88, notes)
