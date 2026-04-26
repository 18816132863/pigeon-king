from __future__ import annotations

from pathlib import Path
from dataclasses import asdict

from .test_plan_generator import TestPlanGenerator
from .self_diagnostics import SelfDiagnostics
from .self_healing_policy import SelfHealingPolicy
from .perfection_gate import PerfectionGate


class SystemSelfTestAgent:
    """Autonomous self-test agent for the V10 personal operating agent.

    It checks whether the system is structurally complete, release-clean,
    registry-consistent, and safe to hand off for real-environment validation.
    """

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)
        self.plan_generator = TestPlanGenerator()
        self.diagnostics = SelfDiagnostics(self.root)
        self.healing_policy = SelfHealingPolicy()
        self.gate = PerfectionGate(self.root)

    def run_extreme_self_test(self) -> dict:
        diagnostic = self.diagnostics.run()
        gate = self.gate.evaluate()
        healing = [
            asdict(self.healing_policy.propose(f.name, f.severity))
            for f in diagnostic.findings
            if f.severity in {"warning", "error"}
        ]
        return {
            "status": "pass" if gate.status == "pass" else "fail",
            "agent_shape": "Self-Evolving Personal Operating Agent",
            "self_test_shape": "Autonomous System Self-Test Agent",
            "test_plan": self.plan_generator.to_dicts(),
            "diagnostics": diagnostic.to_dict(),
            "healing_plan": healing,
            "perfection_gate": gate.to_dict(),
            "real_environment_required": [
                "real_device_runtime",
                "external_account_authorization",
                "API_keys",
                "MCP_servers",
                "long_term_personalization_data",
            ],
        }
