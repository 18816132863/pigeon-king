from __future__ import annotations

from typing import Any

from core.executive_os import ExecutiveOperatingKernel
from core.collaboration import CollaborativeAutonomyKernel
from core.digital_twin import PersonalDigitalTwin
from core.self_governance import ConstitutionalPolicyCore, ValueAlignmentChecker, AutonomyBoundaryManager
from infrastructure.runtime_fabric import RuntimeFabricOrchestrator


class ExecutivePersonalOSOrchestrator:
    """V10.9 executive total-control layer.

    It combines V10.7 collaboration mesh, V10.8 digital twin and V10.9 executive OS kernel.
    """

    def __init__(self) -> None:
        self.executive = ExecutiveOperatingKernel()
        self.collaboration = CollaborativeAutonomyKernel()
        self.twin = PersonalDigitalTwin()
        self.constitution = ConstitutionalPolicyCore()
        self.alignment = ValueAlignmentChecker()
        self.boundary = AutonomyBoundaryManager()
        self.fabric = RuntimeFabricOrchestrator()

    def run(self, command: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
        context = context or {}
        executive = self.executive.operate(command, context.get("reality"))
        collaboration = self.collaboration.run({"objective": command})
        twin = self.twin.build(
            signals=context.get("signals", [{"text": command}]),
            decisions=context.get("decisions", [{"text": command}]),
            feedback=context.get("feedback", []),
            events=context.get("events", [{"text": command}]),
        )
        rules = self.constitution.rules()
        alignment = self.alignment.check({"command": command})
        boundary = self.boundary.boundary(context.get("risk_level", "L2"))
        fabric = self.fabric.orchestrate(context.get("services", []), ["executive", "memory", "runtime"])
        return {
            "status": "executive_personal_os_ready",
            "shape": "Executive Personal OS Agent",
            "executive": executive,
            "collaboration": collaboration,
            "personal_digital_twin": twin,
            "constitutional_rules": rules,
            "alignment": alignment,
            "autonomy_boundary": boundary,
            "runtime_fabric": fabric,
            "done_definition": executive["closure"]["done_definition"],
            "can_claim_done": False,
        }
