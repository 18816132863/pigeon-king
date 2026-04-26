from __future__ import annotations

from .tool_contract_registry import ToolContractRegistry
from .tool_fallback_matrix import ToolFallbackMatrix


class ToolCapabilityNegotiator:
    """Select tools by capability contract, not by blind name matching."""

    def __init__(self) -> None:
        self.registry = ToolContractRegistry()
        self.fallbacks = ToolFallbackMatrix()

    def negotiate(self, required_capability: str, available_tools: list[dict]) -> dict:
        registered = [
            self.registry.register(t.get("tool_id", t.get("name", "tool")), t.get("capabilities", []), t.get("side_effects", []))
            for t in available_tools
        ]
        matrix = self.fallbacks.build(required_capability, registered)
        return {
            "status": "negotiated" if not matrix["missing"] else "capability_missing",
            "registered_tools": registered,
            "fallback_matrix": matrix,
            "requires_acquisition": matrix["missing"],
        }
