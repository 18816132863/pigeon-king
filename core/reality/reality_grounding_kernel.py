from __future__ import annotations

from .fact_state_resolver import FactStateResolver
from .environment_capability_probe import EnvironmentCapabilityProbe
from .uncertainty_manager import UncertaintyManager


class RealityGroundingKernel:
    """Ground every external action in current facts, runtime capability and uncertainty."""

    def __init__(self) -> None:
        self.facts = FactStateResolver()
        self.probe = EnvironmentCapabilityProbe()
        self.uncertainty = UncertaintyManager()

    def ground(self, goal: str, context: dict | None = None) -> dict:
        context = context or {}
        fact_state = self.facts.resolve(context.get("facts", []), context.get("assumptions", []))
        env_state = self.probe.probe(context.get("connectors", []), context.get("device_runtime", {}))
        uncertainty = self.uncertainty.classify({"fact_state": fact_state, "env_state": env_state})
        return {
            "status": "grounded",
            "goal": goal,
            "fact_state": fact_state,
            "environment_state": env_state,
            "uncertainty": uncertainty,
            "execution_grounded": fact_state["can_execute_reality_bound_action"] and env_state["external_execution_possible"],
        }
