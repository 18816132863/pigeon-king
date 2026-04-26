from __future__ import annotations


class CapabilityMarketplace:
    """Trusted catalog interface for stronger skills/capabilities.

    It never installs directly. It only returns candidates with provenance and risk metadata.
    """

    def search(self, capability_gap: str) -> list[dict]:
        return [
            {
                "candidate_id": "trusted_builtin_solution_search",
                "name": "Solution Search Connector",
                "gap": capability_gap,
                "source": "trusted_registry",
                "risk_level": "L2",
                "install_mode": "sandbox_first",
            },
            {
                "candidate_id": "external_api_connector_template",
                "name": "External API Connector Template",
                "gap": capability_gap,
                "source": "template",
                "risk_level": "L3",
                "install_mode": "approval_required",
            },
        ]
