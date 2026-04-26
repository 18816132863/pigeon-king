"""Capability self-extension kernel.

Detects capability gaps and creates a controlled extension plan. It never executes
untrusted installs directly; executable expansion is sandboxed and approval-gated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .solution_search_orchestrator import SolutionSearchOrchestrator
from .external_capability_bus import ExternalCapability, ExternalCapabilityBus


@dataclass
class CapabilityGap:
    gap_id: str
    description: str
    required_for_goal: str
    severity: str = "medium"
    existing_options_checked: list[str] = field(default_factory=list)


class CapabilitySelfExtensionKernel:
    def __init__(self, searcher: SolutionSearchOrchestrator | None = None, bus: ExternalCapabilityBus | None = None) -> None:
        self.searcher = searcher or SolutionSearchOrchestrator()
        self.bus = bus or ExternalCapabilityBus()

    def detect_gap(self, required_capabilities: list[str], available_capabilities: list[str]) -> list[CapabilityGap]:
        available = set(available_capabilities)
        gaps = []
        for cap in required_capabilities:
            if cap not in available:
                gaps.append(CapabilityGap(f"gap_{cap}", f"missing capability: {cap}", cap, "medium", list(available)))
        return gaps

    def build_extension_plan(self, gap: CapabilityGap, auto_mode: bool = True) -> dict[str, Any]:
        search_plan = self.searcher.build_search_plan(gap.description)
        candidates = self.searcher.propose_candidates(gap.required_for_goal)
        extension = {
            "status": "extension_plan_ready",
            "gap": gap.__dict__,
            "auto_mode": auto_mode,
            "search_plan": search_plan,
            "candidates": [c.__dict__ for c in candidates],
            "safety_policy": {
                "no_untrusted_direct_install": True,
                "sandbox_required": True,
                "rollback_required": True,
                "approval_required_for_executable_code": True,
                "promote_only_after_minimal_tests": True,
            },
        }
        # Register safest non-code candidate first if available.
        best = sorted(candidates, key=lambda c: (-c.confidence, c.requires_install))[0]
        cap = ExternalCapability(
            capability_id=gap.gap_id + "_candidate",
            kind="mcp_or_connector" if not best.requires_install else "sandboxed_skill",
            status="candidate",
            risk_level="L3" if best.requires_install else "L2",
            requires_approval=best.requires_install,
            metadata=best.__dict__,
        )
        extension["bus_registration"] = self.bus.register_candidate(cap)
        return extension
