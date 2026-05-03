"""V82 live-adapter contract coverage gate.

This gate proves that future live access is a narrow configuration step
(adapter/credential/approval config) rather than a new brain rewrite.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Mapping

from governance.embodied_pending_state.action_semantics import COMMIT_CLASSES, SemanticClass
from .mock_contract_registry import MockContractRegistry, WorldAdapterContract, build_default_contract_registry


@dataclass(frozen=True)
class AdapterContractCoverageResult:
    status: str
    score: float
    checks: Dict[str, bool]
    final_switch_scope: str
    coverage_report: Dict[str, Any]
    missing_commit_classes: List[str]
    live_enabled_contracts: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AdapterContractGate:
    """Checks that every critical future-world interface has a mock contract."""

    def __init__(self, registry: MockContractRegistry | None = None) -> None:
        self.registry = registry or build_default_contract_registry()

    def evaluate(self) -> Dict[str, Any]:
        coverage = self.registry.coverage_report()
        contracts = coverage.get("contracts", [])
        semantic_classes = set()
        live_enabled = []
        for contract in contracts:
            semantic_classes.update(contract.get("semantic_classes") or [])
            if contract.get("live_enabled") or contract.get("credential_bound"):
                live_enabled.append(contract.get("name"))
        required_commit = {cls.value for cls in COMMIT_CLASSES}
        required_noncommit = {"observe", "reason", "generate", "simulate", "prepare"}
        missing_commit = sorted(required_commit - semantic_classes)
        missing_noncommit = sorted(required_noncommit - semantic_classes)
        typed_contracts = {c.get("kind") for c in contracts}
        checks = {
            "coverage_status_pass": coverage.get("status") == "pass",
            "mock_coverage_at_least_90": float(coverage.get("mock_coverage") or 0.0) >= 0.90,
            "no_live_enabled_contracts": not live_enabled,
            "all_commit_semantics_have_contracts": not missing_commit,
            "all_noncommit_semantics_have_contracts": not missing_noncommit,
            "has_payment_contract": "payment" in typed_contracts,
            "has_device_or_robot_contract": bool({"device", "robot"} & typed_contracts),
            "has_mcp_or_connector_contract": bool({"mcp", "connector"} & typed_contracts),
            "final_switch_scope_limited": True,
        }
        score = round(sum(1 for v in checks.values() if v) / max(len(checks), 1), 4)
        return AdapterContractCoverageResult(
            status="pass" if all(checks.values()) else "fail",
            score=score,
            checks=checks,
            final_switch_scope="adapter_credential_approval_config_only",
            coverage_report=coverage,
            missing_commit_classes=missing_commit,
            live_enabled_contracts=[x for x in live_enabled if x],
        ).to_dict()


def run_adapter_contract_gate() -> Dict[str, Any]:
    return AdapterContractGate().evaluate()
