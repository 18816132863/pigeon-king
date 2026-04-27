"""V52.0 Skill Build Sandbox V5.

Evaluates skill manifests before promotion. No arbitrary install is performed here;
real installation must be separately isolated and approved.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List

@dataclass
class SandboxEvaluationV5:
    candidate_id: str
    passed: bool
    checks: Dict[str, bool]
    recommendation: str
    reasons: List[str]

class SkillBuildSandboxGateV5:
    REQUIRED = {"candidate_id", "source", "tests", "rollback", "risk_tier"}

    def evaluate_manifest(self, manifest: Dict[str, Any]) -> SandboxEvaluationV5:
        checks = {f"has_{k}": k in manifest and bool(manifest[k]) for k in self.REQUIRED}
        checks["risk_not_l4_auto"] = manifest.get("risk_tier") != "L4"
        checks["has_minimum_tests"] = isinstance(manifest.get("tests"), list) and len(manifest.get("tests", [])) >= 1
        passed = all(checks.values())
        reasons = [k for k, ok in checks.items() if not ok]
        recommendation = "promote_to_staging" if passed else "quarantine"
        return SandboxEvaluationV5(candidate_id=str(manifest.get("candidate_id", "unknown")), passed=passed, checks=checks, recommendation=recommendation, reasons=reasons)

    @staticmethod
    def to_dict(evaluation: SandboxEvaluationV5) -> Dict[str, Any]:
        return asdict(evaluation)
