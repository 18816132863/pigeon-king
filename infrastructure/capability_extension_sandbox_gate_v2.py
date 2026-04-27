"""
V25.6 Capability Extension Sandbox Gate V2

Capability self-extension must be gap-driven, trusted-source only, isolated,
tested, risk-scored and reversible before promotion.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ExtensionCandidate:
    name: str
    source: str
    capability_gap: str
    install_mode: str
    has_hash: bool
    test_plan: List[str]
    rollback_plan: List[str]


@dataclass
class ExtensionGateDecision:
    status: str  # promote_candidate, needs_review, quarantine
    reasons: List[str]


TRUSTED_SOURCES = {"builtin_registry", "trusted_connector_catalog", "local_verified_skill_catalog"}


class CapabilityExtensionSandboxGateV2:
    def evaluate(self, candidate: ExtensionCandidate) -> ExtensionGateDecision:
        reasons: List[str] = []
        if not candidate.capability_gap:
            reasons.append("missing_capability_gap")
        if candidate.source not in TRUSTED_SOURCES:
            reasons.append("untrusted_source")
        if candidate.install_mode not in {"no_code_connector", "isolated_venv", "local_skill"}:
            reasons.append("unsafe_install_mode")
        if candidate.install_mode == "isolated_venv" and not candidate.has_hash:
            reasons.append("missing_hash_for_code_install")
        if not candidate.test_plan:
            reasons.append("missing_test_plan")
        if not candidate.rollback_plan:
            reasons.append("missing_rollback_plan")

        if not reasons:
            return ExtensionGateDecision("promote_candidate", ["sandbox_requirements_satisfied"])
        if "untrusted_source" in reasons or "unsafe_install_mode" in reasons:
            return ExtensionGateDecision("quarantine", reasons)
        return ExtensionGateDecision("needs_review", reasons)
