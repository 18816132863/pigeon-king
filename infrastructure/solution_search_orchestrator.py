"""Solution search orchestrator.

In production this can call web/document/API search. In this clean package it emits
auditable search plans and deterministic fallback candidates without network access.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SolutionCandidate:
    source: str
    title: str
    confidence: float
    action: str
    requires_network: bool = False
    requires_install: bool = False


class SolutionSearchOrchestrator:
    def build_search_plan(self, capability_gap: str) -> dict[str, Any]:
        return {
            "status": "search_plan_ready",
            "gap": capability_gap,
            "search_order": [
                "local_skill_registry",
                "local_docs_and_reports",
                "trusted_connectors_or_mcp_catalog",
                "official_api_docs",
                "trusted_package_sources",
                "general_web_search_last",
            ],
            "stop_condition": "candidate_passes_risk_and_minimal_test",
        }

    def propose_candidates(self, capability_gap: str) -> list[SolutionCandidate]:
        gap = capability_gap.lower()
        candidates = [
            SolutionCandidate("local_registry", f"reuse_existing_skill_for_{capability_gap}", 0.55, "reuse_or_wrap_existing_skill"),
            SolutionCandidate("mcp_connector", f"connect_mcp_for_{capability_gap}", 0.72, "register_external_connector", True, False),
            SolutionCandidate("trusted_skill_catalog", f"install_sandboxed_skill_for_{capability_gap}", 0.66, "sandbox_install_then_evaluate", True, True),
        ]
        if "payment" in gap or "支付" in gap:
            for c in candidates:
                c.confidence *= 0.5
        return candidates
