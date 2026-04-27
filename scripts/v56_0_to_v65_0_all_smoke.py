#!/usr/bin/env python3
from pathlib import Path
import sys, json
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent_kernel.v56_to_v65_operating_agent import *

def main():
    contract = MissionContractCompilerV6().compile("设置吃饭提醒并验证结果")
    assert contract.risk_boundary == "L2"
    portfolio = GoalPortfolioV6(); portfolio.add(PortfolioMissionV6("m1", 90)); portfolio.add(PortfolioMissionV6("m2", 10, dependencies=["m1"]))
    assert [m.mission_id for m in portfolio.ready()] == ["m1"]
    portfolio.mark("m1", "completed"); assert [m.mission_id for m in portfolio.ready()] == ["m2"]
    graph = DurableTaskGraphV6([TaskNodeV6("a", "plan"), TaskNodeV6("b", "device", ["a"], is_device_action=True)])
    assert [n.node_id for n in graph.ready()] == ["a"]; graph.complete("a"); assert [n.node_id for n in graph.ready()] == ["b"]
    lane = EndSideSerialLaneV6(); receipt = lane.execute(DeviceActionV6("d1", "modify_alarm", "alarm:1"), lambda a: {"status":"action_timeout"})
    assert receipt["status"] == "timeout_pending_verify" and not lane.locked
    assert DeviceRealitySyncV6().reconcile(receipt, {"target_state_matches": True})["status"] == "success_with_timeout_receipt"
    mem = PersonalMemoryLifecycleV6(); assert mem.commit(MemoryRecordV6("episodic", "modify_alarm timeout needs verification", 0.8))["decision"] == "committed"
    assert CapabilitySupplyChainV6().assess({"source":"local_registry"})["decision"] == "allow_sandbox"
    assert CapabilitySupplyChainV6().assess({"source":"random_url", "requires_code_execution": True, "rollback_supported": False})["decision"] == "quarantine"
    assert AutonomySafetyCaseV6().evaluate({"mission_contract": True})["decision"] == "block"
    assert ScenarioSimulatorV6().run([{"name":"safe"}], lambda s: {"decision":"allow"})["allowed"] == 1
    agent = SelfEvolvingOperatingAgentV6(); assert agent.architecture_layer == "L3 Orchestration"
    assert agent.plan("提醒我吃饭，三路都要")["judge"]["decision"] == "allow"
    assert agent.write_memory("端侧动作必须串行并二次验证", confidence=0.9)["decision"] == "committed"
    report = {"v56_0_to_v65_0_all_smoke": "pass", "count": 10}
    (ROOT / "V56_0_TO_V65_0_SMOKE_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
if __name__ == "__main__":
    main()
