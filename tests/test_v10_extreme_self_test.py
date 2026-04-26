from __future__ import annotations

from core.self_test import SystemSelfTestAgent, PerfectionGate, TestPlanGenerator
from infrastructure.guards import PackageCleanlinessGuard, RegistryConsistencyGuard


def test_extreme_self_test_agent_shape() -> None:
    result = SystemSelfTestAgent(".").run_extreme_self_test()
    assert result["self_test_shape"] == "Autonomous System Self-Test Agent"
    assert result["agent_shape"] == "Self-Evolving Personal Operating Agent"


def test_test_plan_contains_v10_checks() -> None:
    names = [item.name for item in TestPlanGenerator().generate_extreme_plan()]
    assert "v10_agent_shape" in names
    assert "perfection_gate" in names


def test_perfection_gate_returns_structured_decision() -> None:
    result = PerfectionGate(".").evaluate()
    assert result.decision in {"release_candidate", "block"}
    assert 0 <= result.score <= 100


def test_package_cleanliness_guard_contract() -> None:
    result = PackageCleanlinessGuard(".").scan()
    assert "status" in result
    assert "bad_count" in result


def test_registry_consistency_guard_contract() -> None:
    guard = RegistryConsistencyGuard(".")
    assert "status" in guard.check_module_registry()
    assert "status" in guard.check_fusion_index()
