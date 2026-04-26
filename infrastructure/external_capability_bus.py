"""External capability bus for APIs, MCP, connectors, databases and devices."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExternalCapability:
    capability_id: str
    kind: str
    endpoint: str | None = None
    status: str = "candidate"
    risk_level: str = "L2"
    requires_approval: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class ExternalCapabilityBus:
    def __init__(self) -> None:
        self._capabilities: dict[str, ExternalCapability] = {}

    def register_candidate(self, cap: ExternalCapability) -> dict[str, Any]:
        self._capabilities[cap.capability_id] = cap
        return {"status": "registered_candidate", "capability": cap.__dict__}

    def list_candidates(self) -> list[dict[str, Any]]:
        return [cap.__dict__ for cap in self._capabilities.values()]

    def promote(self, capability_id: str, approved: bool = False) -> dict[str, Any]:
        cap = self._capabilities.get(capability_id)
        if cap is None:
            return {"status": "missing", "capability_id": capability_id}
        if cap.requires_approval and not approved:
            return {"status": "approval_required", "capability": cap.__dict__}
        cap.status = "active"
        return {"status": "promoted", "capability": cap.__dict__}
