from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class TestPlanItem:
    name: str
    category: str
    command: str
    required: bool = True
    timeout_seconds: int = 120
    side_effect_free: bool = True


class TestPlanGenerator:
    """Generate deterministic self-test plans for the personal autonomous OS agent."""

    def generate_extreme_plan(self) -> list[TestPlanItem]:
        return [
            TestPlanItem("v10_agent_shape", "v10_core", "python scripts/check_v10_autonomous_agent.py"),
            TestPlanItem("v10_self_extension", "v10_core", "python scripts/v10_self_extension_smoke.py"),
            TestPlanItem("v10_core_tests", "tests", "python -m pytest tests/test_v10_autonomous_agent.py -q"),
            TestPlanItem("route_registry", "registry", "python scripts/check_route_registry.py"),
            TestPlanItem("system_integrity", "integrity", "python scripts/system_integrity_check.py"),
            TestPlanItem("orphan_components", "integrity", "python scripts/find_orphan_components.py"),
            TestPlanItem("extreme_self_test", "self_test", "python scripts/run_v10_extreme_self_test.py --internal-only"),
            TestPlanItem("perfection_gate", "gate", "python scripts/check_v10_perfection_gate.py"),
        ]

    def to_dicts(self) -> list[dict]:
        return [asdict(item) for item in self.generate_extreme_plan()]
