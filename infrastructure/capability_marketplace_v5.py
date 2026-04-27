"""V51.0 Trusted Capability Marketplace V5.

Controlled catalog for local, device, connector and MCP-like capabilities.
It does not install arbitrary code; it ranks trusted candidates for the sandbox gate.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, List, Any

@dataclass
class CapabilityCandidateV5:
    capability_id: str
    source_type: str
    trust_level: str
    description: str
    requires_install: bool = False
    risk_tier: str = "L2"

class TrustedCapabilityMarketplaceV5:
    TRUST_ORDER = {"builtin": 0, "trusted_connector": 1, "trusted_package": 2, "unknown": 9}

    def __init__(self) -> None:
        self._candidates: Dict[str, CapabilityCandidateV5] = {}

    def register(self, candidate: CapabilityCandidateV5) -> None:
        self._candidates[candidate.capability_id] = candidate

    def search(self, text: str) -> List[Dict[str, Any]]:
        text = text.lower().strip()
        matched = [c for c in self._candidates.values() if text in c.description.lower() or text in c.capability_id.lower()]
        matched.sort(key=lambda c: (self.TRUST_ORDER.get(c.trust_level, 9), c.requires_install, c.risk_tier))
        return [asdict(c) for c in matched]
