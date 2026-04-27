"""V71.0 Skill supply-chain SBOM and attestation checks."""
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class SkillArtifact:
    name: str
    version: str
    source: str
    hashes_present: bool = False
    tests_present: bool = False
    rollback_present: bool = False
    permissions: List[str] = field(default_factory=list)

class SkillSupplyChainAttestor:
    layer = "L6_INFRASTRUCTURE"
    TRUSTED_SOURCES = {"local_registry", "trusted_catalog", "signed_internal"}

    def attest(self, artifact: SkillArtifact) -> Dict[str, object]:
        issues = []
        if artifact.source not in self.TRUSTED_SOURCES:
            issues.append("untrusted_source")
        if not artifact.hashes_present:
            issues.append("missing_hashes")
        if not artifact.tests_present:
            issues.append("missing_tests")
        if not artifact.rollback_present:
            issues.append("missing_rollback")
        if "install_code" in artifact.permissions:
            issues.append("requires_human_approval")
        return {"status": "pass" if not issues else "quarantine", "issues": issues}
