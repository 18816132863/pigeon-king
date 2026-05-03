"""Mock-first skill extension sandbox."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Mapping
from governance.embodied_pending_state import classify_action_semantics

TRUSTED_SOURCE_TYPES = {"builtin", "local_registry", "trusted_mcp", "approved_connector", "signed_package"}

@dataclass
class SkillCandidate:
    name: str
    source_type: str = "local_registry"
    semantic_class: str = "prepare"
    provenance: str = "declared"
    tests: List[str] = field(default_factory=list)
    has_hash_or_signature: bool = False
    wants_live_credentials: bool = False
    wants_network: bool = False
    wants_filesystem_write: bool = False
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class SandboxPromotionDecision:
    accepted_to_sandbox: bool
    promoted_to_active: bool
    promoted_to_live: bool
    mode: str
    reason: str
    required_next_steps: List[str]
    candidate: Dict[str, Any]
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class SkillExtensionSandbox:
    def evaluate_candidate(self, candidate: Mapping[str, Any] | SkillCandidate) -> SandboxPromotionDecision:
        c = candidate.to_dict() if isinstance(candidate, SkillCandidate) else dict(candidate or {})
        action_semantic = classify_action_semantics(c)
        source_ok = str(c.get("source_type") or "") in TRUSTED_SOURCE_TYPES
        signed_ok = bool(c.get("has_hash_or_signature") or c.get("source_type") in {"builtin", "local_registry", "trusted_mcp", "approved_connector"})
        tests = list(c.get("tests") or [])
        tests_ok = len(tests) >= 2 or str(c.get("source_type")) in {"builtin", "local_registry"}
        live_demand = bool(c.get("wants_live_credentials") or c.get("wants_network") or c.get("wants_filesystem_write"))
        if action_semantic.is_commit_action:
            return SandboxPromotionDecision(True, False, False, "commit_skill_mock_only", "commit_related_skills_can_only_be_registered_as_mock_contracts_in_pending_access_state", ["create_mock_contract", "add_commit_barrier_test", "manual_policy_review"], {**c, "classified_semantic": action_semantic.to_dict()})
        if not source_ok or not signed_ok:
            return SandboxPromotionDecision(False, False, False, "rejected_untrusted_or_unsigned_source", "self_extension_requires_trusted_source_and_hash_or_signature", ["use_trusted_registry", "attach_hash_or_signature", "rerun_sandbox_eval"], {**c, "classified_semantic": action_semantic.to_dict()})
        if live_demand:
            return SandboxPromotionDecision(True, False, False, "sandbox_only_live_request_blocked", "candidate_requests_live_network_credentials_or_filesystem_write_before_freeze_boundary_is_opened", ["replace_live_dependency_with_mock", "run_contract_tests", "request_human_review"], {**c, "classified_semantic": action_semantic.to_dict()})
        return SandboxPromotionDecision(True, tests_ok, False, "active_sandbox_skill" if tests_ok else "sandbox_candidate_needs_tests", "non_commit_skill_can_be_promoted_to_active_sandbox_without_live_side_effects" if tests_ok else "candidate_needs_minimum_tests_before_active_use", [] if tests_ok else ["add_minimum_unit_test", "add_trace_replay_test"], {**c, "classified_semantic": action_semantic.to_dict()})

def evaluate_skill_candidate(candidate: Mapping[str, Any] | SkillCandidate) -> Dict[str, Any]:
    return SkillExtensionSandbox().evaluate_candidate(candidate).to_dict()
