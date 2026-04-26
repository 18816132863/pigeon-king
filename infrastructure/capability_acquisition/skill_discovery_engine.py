from __future__ import annotations

from .trusted_source_policy import TrustedSourcePolicy


class SkillDiscoveryEngine:
    """Discover candidate skills/solutions without installing them."""

    def __init__(self) -> None:
        self.policy = TrustedSourcePolicy()

    def discover(self, gap: str) -> dict:
        candidates = [
            {"name": "builtin_solution_search", "source_type": "builtin", "risk_level": "L1"},
            {"name": "mcp_connector_template", "source_type": "local_template", "risk_level": "L2"},
            {"name": "external_package_candidate", "source_type": "unknown_external", "risk_level": "L3"},
        ]
        evaluated = [{**c, "policy": self.policy.evaluate_source(c["source_type"], c["risk_level"])} for c in candidates]
        return {"status": "candidates_discovered", "gap": gap, "candidates": evaluated}
