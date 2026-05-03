#!/usr/bin/env python3
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import json, tempfile
from pathlib import Path
from core.mission.autonomy_horizon_planner_v7 import MultiHorizonPlanner, HorizonGoal
from infrastructure.evidence_proof_ledger_v7 import EvidenceProofLedger
from execution.device_conflict_resolver_v7 import DeviceConflictResolver, DeviceActionRequest
from memory_context.preference_evolution_model_v7 import PreferenceEvolutionModel, PreferenceSignal
from governance.policy.connector_governance_broker_v7 import ConnectorGovernanceBroker, ConnectorRequest
from infrastructure.skill_supply_chain_attestation_v7 import SkillSupplyChainAttestor, SkillArtifact
from orchestration.proactive_opportunity_detector_v7 import ProactiveOpportunityDetector, Opportunity
from infrastructure.cross_session_mission_continuity_v7 import MissionContinuityStore, ContinuityState
from agent_kernel.rollback_repair_planner_v7 import RollbackRepairPlanner, FailureEvent
from agent_kernel.self_evolving_os_command_center_v7 import SelfEvolvingOSCommandCenter

def main():
    planner = MultiHorizonPlanner()
    plan = planner.plan([HorizonGoal("g2", "weekly", "week", 5), HorizonGoal("g1", "now", "now", 9)])
    assert plan.execution_order[0] == "g1"

    ledger = EvidenceProofLedger()
    ev = ledger.add("a1", "receipt", {"ok": True})
    assert ledger.verify_exists("a1", "receipt") and ev.payload_hash

    resolver = DeviceConflictResolver()
    a1 = DeviceActionRequest("alarm", "alarm")
    a2 = DeviceActionRequest("notify", "notification", depends_on=["alarm"])
    assert resolver.start(a1) == "started"
    assert resolver.start(a2) == "blocked_by_serial_lane_or_dependency"
    resolver.finish(a1, "timeout_pending_verify")
    assert resolver.start(a2) == "blocked_by_serial_lane_or_dependency"
    resolver.verify_pending("alarm", True)
    assert resolver.start(a2) == "started"

    mem = PreferenceEvolutionModel()
    assert mem.apply(PreferenceSignal("delivery_style", "direct")) == "applied"

    gov = ConnectorGovernanceBroker()
    assert gov.evaluate(ConnectorRequest("c1", "send", ["send_external"], remote=True, writes_external=True))["decision"] == "confirm"

    att = SkillSupplyChainAttestor()
    assert att.attest(SkillArtifact("s", "1", "trusted_catalog", True, True, True))["status"] == "pass"

    detector = ProactiveOpportunityDetector()
    prop = detector.propose([Opportunity("o1", "draft", 5, 1), Opportunity("o2", "send", 9, 4, True)])
    assert prop["top"] == "o1" and prop["mode"] == "propose_not_execute"

    with tempfile.TemporaryDirectory() as td:
        store = MissionContinuityStore(Path(td) / "state.json")
        store.save(ContinuityState("m1", ["s1"], ["s2"], "s1", ["ev1"]))
        assert store.resume_instruction()["resume_from"] == "s2"

    repair = RollbackRepairPlanner().plan(FailureEvent("a1", "action_timeout", side_effect=True))
    assert repair["next"] == "verify_before_retry"

    report = SelfEvolvingOSCommandCenter().summarize({
        "agent_kernel_layer_is_l3": True,
        "device_serial_lane": True,
        "memory_guard": True,
        "extension_supply_chain": True,
    })
    assert report.mission_status == "ready" and report.layer == "L3_ORCHESTRATION"

    print(json.dumps({"v66_0_to_v75_0_all_smoke": "pass", "count": 10}, ensure_ascii=False))

if __name__ == "__main__":
    main()
