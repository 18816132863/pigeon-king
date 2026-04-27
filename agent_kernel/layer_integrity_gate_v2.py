"""
V25.1 Layer Integrity Gate V2

Keeps six-layer architecture stable:
L1 Core, L2 Memory Context, L3 Orchestration, L4 Execution,
L5 Governance, L6 Infrastructure.

agent_kernel is a L3 orchestration hub, not L7.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


ALLOWED_LAYERS = {
    "L1 Core",
    "L2 Memory Context",
    "L3 Orchestration",
    "L4 Execution",
    "L5 Governance",
    "L6 Infrastructure",
}


@dataclass
class LayerGateResult:
    ok: bool
    violations: List[str]


class LayerIntegrityGateV2:
    def check_manifest(self, manifest: Dict[str, str]) -> LayerGateResult:
        violations: List[str] = []
        for module, layer in manifest.items():
            if layer not in ALLOWED_LAYERS:
                violations.append(f"{module}: invalid layer {layer}")
            if module.startswith("agent_kernel") and layer != "L3 Orchestration":
                violations.append(f"{module}: agent_kernel must belong to L3 Orchestration")
        return LayerGateResult(ok=not violations, violations=violations)
