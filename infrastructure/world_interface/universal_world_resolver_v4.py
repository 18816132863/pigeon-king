"""V31.0 Universal World Resolver V4.

World interface layer within the six-layer model:
- It is not a new architecture layer.
- It resolves local capability / device / connector / api / mcp-like resources.
- It produces contracts; execution still goes through L4 and governance through L5.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any


@dataclass
class CapabilityEndpoint:
    name: str
    endpoint_type: str  # local / device / connector / api / mcp
    trust_level: str  # trusted / reviewed / untrusted
    requires_approval: bool = False
    side_effect: bool = False
    device_side_effect: bool = False
    status: str = "active"

    def to_dict(self):
        return asdict(self)


class UniversalWorldResolverV4:
    def __init__(self):
        self.endpoints: Dict[str, CapabilityEndpoint] = {}

    def register(self, endpoint: CapabilityEndpoint) -> None:
        self.endpoints[endpoint.name] = endpoint

    def resolve(self, capability_name: str, *, allow_untrusted: bool = False) -> Dict[str, Any]:
        endpoint = self.endpoints.get(capability_name)
        if not endpoint:
            return {"status": "missing", "reason": "capability_not_registered", "capability": capability_name}
        if endpoint.status != "active":
            return {"status": "unavailable", "reason": endpoint.status, "endpoint": endpoint.to_dict()}
        if endpoint.trust_level == "untrusted" and not allow_untrusted:
            return {"status": "requires_review", "reason": "untrusted_endpoint", "endpoint": endpoint.to_dict()}
        controls = ["trace", "audit"]
        if endpoint.requires_approval:
            controls.append("approval")
        if endpoint.side_effect:
            controls.append("idempotency")
        if endpoint.device_side_effect:
            controls.append("global_device_serial")
        return {"status": "resolved", "endpoint": endpoint.to_dict(), "controls": controls}

    def find_candidates(self, intent: str) -> List[Dict[str, Any]]:
        terms = set(intent.lower().split())
        results = []
        for ep in self.endpoints.values():
            if ep.status != "active":
                continue
            score = sum(1 for t in terms if t and t in ep.name.lower())
            if score or ep.endpoint_type in intent.lower():
                results.append({"score": score, "endpoint": ep.to_dict()})
        return sorted(results, key=lambda x: x["score"], reverse=True)
