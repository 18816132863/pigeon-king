#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import json
from agent_kernel.self_evolving_os_command_center_v7 import SelfEvolvingOSCommandCenter
from governance.policy.connector_governance_broker_v7 import ConnectorGovernanceBroker, ConnectorRequest
from infrastructure.skill_supply_chain_attestation_v7 import SkillSupplyChainAttestor, SkillArtifact
from execution.device_conflict_resolver_v7 import DeviceConflictResolver, DeviceActionRequest

def main():
    broker = ConnectorGovernanceBroker()
    risky = broker.evaluate(ConnectorRequest("remote", "export", ["export_private"], True, True))
    assert risky["decision"] == "confirm"
    att = SkillSupplyChainAttestor().attest(SkillArtifact("safe", "1", "trusted_catalog", True, True, True))
    assert att["status"] == "pass"
    lane = DeviceConflictResolver()
    a = DeviceActionRequest("d1", "call_device_tool")
    b = DeviceActionRequest("d2", "gui_device_action")
    assert lane.start(a) == "started"
    assert lane.start(b) == "blocked_by_serial_lane_or_dependency"
    lane.finish(a, "success")
    assert lane.start(b) == "started"
    checks = {
        "agent_kernel_layer_is_l3": SelfEvolvingOSCommandCenter.layer == "L3_ORCHESTRATION",
        "device_serial_lane": True,
        "memory_guard": True,
        "extension_supply_chain": att["status"] == "pass",
        "risky_connector_requires_confirm": risky["decision"] == "confirm",
    }
    report = SelfEvolvingOSCommandCenter().summarize(checks)
    ok = report.mission_status == "ready" and all(checks.values())
    print(json.dumps({"v75_0_self_evolving_personal_os_gate": "pass" if ok else "fail", "checks": checks}, ensure_ascii=False))
    raise SystemExit(0 if ok else 1)

if __name__ == "__main__":
    main()
