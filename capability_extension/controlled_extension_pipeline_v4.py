"""V32.0 Controlled Extension Pipeline V4.

Capability self-extension is allowed only as:
gap -> existing search -> reviewed candidate -> sandbox test -> risk decision -> promotion/quarantine.

This module does not install packages itself; it emits a controlled plan and evaluates mock/sandbox outcomes.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Any
import hashlib


@dataclass
class CapabilityGap:
    gap_id: str
    requested_capability: str
    existing_checked: bool
    severity: str


@dataclass
class ExtensionCandidate:
    name: str
    source: str
    trust_level: str
    requires_code_execution: bool
    hash_pinned: bool = False
    rollback_ready: bool = False

    def to_dict(self):
        return asdict(self)


class ControlledExtensionPipelineV4:
    trusted_sources = {"internal_registry", "reviewed_connector", "reviewed_mcp", "vendor_signed"}

    def detect_gap(self, requested_capability: str, available: List[str]) -> Dict[str, Any]:
        if requested_capability in available:
            return {"gap": False, "reason": "capability_already_available"}
        gap_id = "gap_" + hashlib.sha256(requested_capability.encode("utf-8")).hexdigest()[:12]
        return {"gap": True, "record": asdict(CapabilityGap(gap_id, requested_capability, True, "medium"))}

    def evaluate_candidate(self, candidate: ExtensionCandidate) -> Dict[str, Any]:
        if candidate.source not in self.trusted_sources:
            return {"decision": "quarantine", "reason": "source_not_trusted", "candidate": candidate.to_dict()}
        if candidate.requires_code_execution and not (candidate.hash_pinned and candidate.rollback_ready):
            return {"decision": "reject", "reason": "code_execution_without_hash_or_rollback", "candidate": candidate.to_dict()}
        controls = ["sandbox_test", "min_smoke", "audit"]
        if candidate.requires_code_execution:
            controls.extend(["hash_verify", "rollback_test", "approval"])
        return {"decision": "candidate_ok", "controls": controls, "candidate": candidate.to_dict()}

    def promote_after_test(self, candidate: ExtensionCandidate, test_passed: bool, risk_approved: bool) -> Dict[str, Any]:
        evaluated = self.evaluate_candidate(candidate)
        if evaluated["decision"] != "candidate_ok":
            return evaluated
        if not test_passed:
            return {"decision": "quarantine", "reason": "sandbox_test_failed"}
        if candidate.requires_code_execution and not risk_approved:
            return {"decision": "pending_approval", "reason": "code_extension_needs_approval"}
        return {"decision": "promote_active", "reason": "tests_passed_and_controls_satisfied"}
