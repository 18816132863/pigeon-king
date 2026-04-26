from __future__ import annotations

from .capability_marketplace import CapabilityMarketplace


class SolutionAcquisitionPipeline:
    """Search → evaluate → sandbox plan → approval gate → register experimental."""

    def __init__(self) -> None:
        self.marketplace = CapabilityMarketplace()

    def build_pipeline(self, gap: str) -> dict:
        candidates = self.marketplace.search(gap)
        return {
            "status": "acquisition_plan_ready",
            "gap": gap,
            "candidates": candidates,
            "pipeline": [
                "search_trusted_sources",
                "evaluate_candidate_risk",
                "generate_sandbox_adapter",
                "run_minimal_tests",
                "prepare_rollback",
                "request_approval_if_L3_or_above",
                "register_as_experimental",
            ],
            "safety": {
                "no_direct_untrusted_install": True,
                "sandbox_required": True,
                "approval_required_for_external_code": True,
                "rollback_required": True,
            },
        }
