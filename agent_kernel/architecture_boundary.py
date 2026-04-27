"""
V23.2 Six-Layer Architecture Boundary Guard.

Purpose:
- Keep the architecture fixed at six layers.
- Treat agent_kernel / 自治器官 as the L3 Orchestration autonomous hub.
- Prevent documentation, reports, or future modules from promoting agent_kernel to L7.

This module is intentionally dependency-light so it can run in old workspaces.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Tuple

ALLOWED_LAYERS: Tuple[str, ...] = (
    "L1 Core",
    "L2 Memory Context",
    "L3 Orchestration",
    "L4 Execution",
    "L5 Governance",
    "L6 Infrastructure",
)

MODULE_LAYER_MAP: Dict[str, str] = {
    "core": "L1 Core",
    "memory_context": "L2 Memory Context",
    "orchestration": "L3 Orchestration",
    "agent_kernel": "L3 Orchestration",
    "autonomous_planner": "L3 Orchestration",
    "execution": "L4 Execution",
    "platform_adapter": "L4 Execution",
    "governance": "L5 Governance",
    "safety_governor": "L5 Governance",
    "infrastructure": "L6 Infrastructure",
}

FORBIDDEN_LAYER_TOKENS: Tuple[str, ...] = (
    "L7",
    "第七层",
    "七层主架构",
    "agent_kernel layer",
    "Agent Kernel Layer",
)


@dataclass(frozen=True)
class ArchitectureViolation:
    subject: str
    reason: str
    expected: str
    actual: str = ""

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ArchitectureBoundaryReport:
    passed: bool
    layer_count: int
    agent_kernel_layer: str
    violations: List[Dict[str, str]]

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def get_module_layer(module_name: str) -> str:
    """Return the canonical six-layer ownership for a top-level module."""
    top = (module_name or "").split("/", 1)[0].split(".", 1)[0]
    return MODULE_LAYER_MAP.get(top, "UNKNOWN")


def validate_module_layers(module_names: Iterable[str]) -> List[ArchitectureViolation]:
    violations: List[ArchitectureViolation] = []
    for name in module_names:
        layer = get_module_layer(name)
        if layer == "UNKNOWN":
            continue
        if layer not in ALLOWED_LAYERS:
            violations.append(
                ArchitectureViolation(
                    subject=name,
                    reason="module mapped outside the fixed six-layer architecture",
                    expected="; ".join(ALLOWED_LAYERS),
                    actual=layer,
                )
            )
        if name.split("/", 1)[0] == "agent_kernel" and layer != "L3 Orchestration":
            violations.append(
                ArchitectureViolation(
                    subject=name,
                    reason="agent_kernel must not become an independent seventh layer",
                    expected="L3 Orchestration",
                    actual=layer,
                )
            )
    return violations


def scan_text_for_forbidden_layers(text: str, subject: str = "text") -> List[ArchitectureViolation]:
    violations: List[ArchitectureViolation] = []
    for token in FORBIDDEN_LAYER_TOKENS:
        if token in (text or ""):
            violations.append(
                ArchitectureViolation(
                    subject=subject,
                    reason=f"forbidden layer token found: {token}",
                    expected="agent_kernel is an L3 Orchestration autonomous hub, not L7",
                    actual=token,
                )
            )
    return violations


def build_architecture_boundary_report(extra_modules: Iterable[str] = ()) -> ArchitectureBoundaryReport:
    modules = list(MODULE_LAYER_MAP.keys()) + list(extra_modules)
    violations = validate_module_layers(modules)
    return ArchitectureBoundaryReport(
        passed=not violations,
        layer_count=len(ALLOWED_LAYERS),
        agent_kernel_layer=MODULE_LAYER_MAP["agent_kernel"],
        violations=[v.to_dict() for v in violations],
    )
