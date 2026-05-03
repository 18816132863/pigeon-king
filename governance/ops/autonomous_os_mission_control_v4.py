"""V35.0 Autonomous OS Mission Control V4.

The top-level integration/gate.
It coordinates contracts, workflow, judge, world resolver, memory, extension and evaluation,
while preserving six-layer boundaries.
"""
from __future__ import annotations

from typing import Dict, Any

from core.operating_contract_v3 import GoalContractCompilerV3
from orchestration.durable_workflow_engine_v3 import DurableWorkflowCompilerV3
from governance.constitutional_judge_v4 import ConstitutionalJudgeV4
from memory_context.personal_memory_kernel_v4 import PersonalMemoryKernelV4
from infrastructure.world_interface.universal_world_resolver_v4 import UniversalWorldResolverV4, CapabilityEndpoint
from infrastructure.capability_extension.controlled_extension_pipeline_v4 import ControlledExtensionPipelineV4, ExtensionCandidate
from evaluation.autonomy_regression_matrix_v4 import AutonomyRegressionMatrixV4
from core.personality.persona_drift_guard_v4 import PersonaDriftGuardV4


class AutonomousOSMissionControlV4:
    def __init__(self):
        self.goal_compiler = GoalContractCompilerV3()
        self.workflow_compiler = DurableWorkflowCompilerV3()
        self.judge = ConstitutionalJudgeV4()
        self.memory = PersonalMemoryKernelV4()
        self.world = UniversalWorldResolverV4()
        self.extension = ControlledExtensionPipelineV4()
        self.evaluator = AutonomyRegressionMatrixV4()
        self.persona_guard = PersonaDriftGuardV4()

        self.world.register(CapabilityEndpoint(
            name="device_alarm_modify",
            endpoint_type="device",
            trust_level="trusted",
            side_effect=True,
            device_side_effect=True,
        ))
        self.world.register(CapabilityEndpoint(
            name="local_planner",
            endpoint_type="local",
            trust_level="trusted",
            side_effect=False,
        ))

    def run_gate(self) -> Dict[str, Any]:
        contract = self.goal_compiler.compile("明天早上8点提醒我吃饭，端侧多动作必须串行，并把经验写回。")
        graph = self.workflow_compiler.build_from_contract(contract)
        graph_serial = graph.assert_device_actions_serialized()

        judge_decision = self.judge.judge("device_action", {
            "side_effect": True,
            "device_side_effect": True,
            "confidence": 0.92,
        })

        memory_result = self.memory.write(
            "procedural",
            "端侧多动作必须走全局串行队列，超时后先二次验证，不直接判离线。",
            confidence=0.95,
            source="task_verified",
            tags=["device", "serial", "timeout_verify"],
        )

        world_result = self.world.resolve("device_alarm_modify")

        gap = self.extension.detect_gap("new_safe_connector", available=["device_alarm_modify", "local_planner"])
        candidate_result = self.extension.evaluate_candidate(ExtensionCandidate(
            name="new_safe_connector",
            source="reviewed_connector",
            trust_level="reviewed",
            requires_code_execution=False,
            rollback_ready=True,
        ))

        persona = self.persona_guard.check_response_plan({
            "creates_L7": False,
            "high_risk_auto_execute_without_approval": False,
            "long_task_without_state": False,
            "asks_unnecessary_clarification": False,
        })

        eval_result = self.evaluator.evaluate({
            "contract_id": contract.contract_id,
            "risk_boundary": contract.risk_boundary,
            "done_definition": contract.objectives[0].done_definition,
            "global_device_serial": graph_serial,
            "pending_verify_blocks_dependent": True,
            "judge_decision": judge_decision.decision,
            "required_controls": judge_decision.required_controls,
            "memory_status": memory_result["status"],
            "pollution_prevented": True,
            "gap_detected": gap["gap"],
            "sandbox_required": candidate_result["decision"] == "candidate_ok",
            "rollback_required": "audit" in candidate_result.get("controls", []),
        })

        checks = {
            "contract": bool(contract.contract_id and contract.objectives),
            "graph_serial": graph_serial,
            "judge_controls_device_serial": "global_device_serial_lane" in judge_decision.required_controls,
            "memory_guarded": memory_result["status"] == "written",
            "world_resolved": world_result["status"] == "resolved",
            "extension_controlled": candidate_result["decision"] == "candidate_ok",
            "persona_stable": persona["pass"],
            "eval_pass": eval_result["pass"],
        }
        return {
            "autonomous_os_gate": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "contract": contract.to_dict(),
            "graph": graph.to_dict(),
            "judge": judge_decision.to_dict(),
            "memory": memory_result,
            "world": world_result,
            "extension": candidate_result,
            "persona": persona,
            "evaluation": eval_result,
        }
