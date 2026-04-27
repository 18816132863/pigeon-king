#!/usr/bin/env python3
from pathlib import Path
import sys
import json
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_kernel.layer_integrity_gate_v2 import LayerIntegrityGateV2
from platform_adapter.world_interface_resolver_v2 import WorldInterface, WorldInterfaceResolverV2
from infrastructure.capability_extension_sandbox_gate_v2 import CapabilityExtensionSandboxGateV2, ExtensionCandidate
from agent_kernel.personal_operating_loop_v2 import PersonalOperatingLoopV2

layer_gate = LayerIntegrityGateV2()
layer_result = layer_gate.check_manifest({
    "agent_kernel/personal_operating_loop_v2.py": "L3 Orchestration",
    "memory_context/memory_writeback_guard_v2.py": "L2 Memory Context",
    "governance/policy/device_action_contract_policy.py": "L5 Governance",
    "orchestration/durable_task_graph_v2.py": "L3 Orchestration",
    "execution/device_timeout_receipt_verifier_v2.py": "L4 Execution",
    "infrastructure/capability_extension_sandbox_gate_v2.py": "L6 Infrastructure",
})

resolver = WorldInterfaceResolverV2()
resolver.register(WorldInterface("device_alarm", "device", "builtin", ["alarm.search", "alarm.modify"]))

extension_decision = CapabilityExtensionSandboxGateV2().evaluate(ExtensionCandidate(
    name="device_alarm_builtin",
    source="builtin_registry",
    capability_gap="alarm.modify",
    install_mode="local_skill",
    has_hash=False,
    test_plan=["alarm_modify_timeout_verify"],
    rollback_plan=["disable_route"],
))

loop_result = PersonalOperatingLoopV2().plan("明天 8 点用三种方式提醒我吃饭", [
    {"node_id": "alarm", "action": "modify_alarm", "end_side": True},
    {"node_id": "push", "action": "hiboard_push", "end_side": True},
    {"node_id": "cron", "action": "chat_cron", "end_side": False},
])

gate = {
    "gate": "V25.7 Personal Operating Agent Gate",
    "status": "pass" if layer_result.ok and resolver.has_capability("alarm.modify") and extension_decision.status == "promote_candidate" and loop_result.status == "planned" else "fail",
    "layer_gate": layer_result.__dict__,
    "world_interface_alarm": resolver.has_capability("alarm.modify"),
    "extension_gate_status": extension_decision.status,
    "operating_loop": loop_result.to_dict(),
    "updated_at": time.time(),
}
Path("V25_7_PERSONAL_OPERATING_AGENT_GATE.json").write_text(json.dumps(gate, ensure_ascii=False, indent=2), encoding="utf-8")
assert gate["status"] == "pass", gate
print("v25_7_personal_operating_agent_gate: pass")
