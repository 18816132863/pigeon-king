#!/usr/bin/env python3
from __future__ import annotations
import json
import tempfile
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.goal_portfolio_v5 import GoalContractV5, GoalPortfolioV5
from infrastructure.run_ledger_v5 import DurableRunLedgerV5
from execution.device_reality_sync_v5 import DeviceActionV5, DeviceRealitySyncV5, SUCCESS_WITH_TIMEOUT_RECEIPT
from memory_context.personal_knowledge_graph_v5 import PersonalKnowledgeGraphV5, MemoryNodeV5
from governance.human_approval_interrupt_v5 import HumanApprovalInterruptV5
from infrastructure.capability_marketplace_v5 import TrustedCapabilityMarketplaceV5, CapabilityCandidateV5
from infrastructure.skill_build_sandbox_v5 import SkillBuildSandboxGateV5
from evaluation.continuous_learning_evaluator_v5 import ContinuousLearningEvaluatorV5
from ops.mission_control_dashboard_v5 import MissionControlDashboardV5


def main() -> int:
    goal = GoalContractV5.build("三路提醒并验证结果", horizon="today", priority=90, approval_points=["before_external_send"])
    portfolio = GoalPortfolioV5(); portfolio.add(goal)
    assert portfolio.next_goal().goal_id == goal.goal_id

    with tempfile.TemporaryDirectory() as d:
        ledger = DurableRunLedgerV5(Path(d) / "run_ledger.json")
        run_id = ledger.new_run_id()
        ledger.append(run_id, "status", {"status": "running"})
        ledger.append(run_id, "step_completed", {"step": "goal_compiled"})
        ledger.append(run_id, "pending_steps", {"pending_steps": ["device_action", "verify", "memory_writeback"]})
        assert ledger.latest_state(run_id)["status"] == "running"

    lane = DeviceRealitySyncV5()
    actions = [
        DeviceActionV5("a1", "alarm.modify", {"title": "吃饭提醒"}, "idem_alarm_1", "modify_alarm_90s"),
        DeviceActionV5("a2", "notification.push", {"body": "吃饭"}, "idem_push_1"),
    ]
    def executor(action):
        return {"status": "timeout" if action.action_id == "a1" else "success", "device_connected": True}
    def verifier(action, raw):
        return True
    receipts = lane.execute_serial(actions, executor, verifier)
    assert receipts[0].status == SUCCESS_WITH_TIMEOUT_RECEIPT
    assert receipts[1].status == "success"

    graph = PersonalKnowledgeGraphV5()
    assert graph.add_node(MemoryNodeV5("n1", "procedural", "端侧超时先验证再重试", 0.9))
    assert not graph.add_node(MemoryNodeV5("n2", "preference", "", 0.2))

    approval = HumanApprovalInterruptV5()
    packet = approval.create("L3", "发送外部消息", {"target": "external"})
    assert approval.resume(packet, "approved")["can_continue"] is True

    market = TrustedCapabilityMarketplaceV5()
    market.register(CapabilityCandidateV5("local_alarm", "device", "builtin", "alarm reminder device ability"))
    assert market.search("alarm")[0]["capability_id"] == "local_alarm"

    sandbox = SkillBuildSandboxGateV5()
    evaluation = sandbox.evaluate_manifest({"candidate_id": "c1", "source": "trusted", "tests": ["smoke"], "rollback": "snapshot", "risk_tier": "L2"})
    assert evaluation.passed

    suggestions = ContinuousLearningEvaluatorV5().evaluate_run({"device_action_timeout_verified": True, "user_prefers_full_packages": True})
    assert len(suggestions) == 2

    report = MissionControlDashboardV5().build_report({
        "goal": {"status": "pass"},
        "workflow": {"status": "pass"},
        "device_lane": {"status": "pass"},
        "governance": {"status": "pass"},
        "memory": {"status": "pass"},
        "extension": {"status": "pass"},
    })
    assert report["status"] == "pass"

    out = ROOT / "V46_0_TO_V55_0_SMOKE_REPORT.json"
    out.write_text(json.dumps({"v46_0_to_v55_0_all_smoke": "pass", "count": 10, "dashboard": report}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("v46_0_to_v55_0_all_smoke: pass")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
