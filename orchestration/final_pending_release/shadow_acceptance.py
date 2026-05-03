"""V84 shadow scenario acceptance for final pending-access readiness."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Iterable, List, Mapping

from governance.embodied_pending_state.action_semantics import classify_action_semantics
from governance.embodied_pending_state.commit_barrier import CommitBarrier
from infrastructure.world_interface.adapter_contract_gate import AdapterContractGate


@dataclass(frozen=True)
class ShadowScenarioResult:
    scenario_id: str
    status: str
    actions_checked: int
    commit_actions_paused: int
    non_commit_actions_allowed: int
    real_side_effects: int
    notes: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ShadowScenarioAcceptanceSuite:
    """Runs business/digital/embodied mock scenarios without live side effects."""

    def __init__(self) -> None:
        self.barrier = CommitBarrier()

    def run_scenario(self, scenario_id: str, actions: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
        checked = 0
        paused = 0
        allowed = 0
        for action in actions:
            checked += 1
            result = self.barrier.check(action)
            semantic = classify_action_semantics(action)
            if semantic.is_commit_action and not result.allowed and result.real_side_effect_allowed is False:
                paused += 1
            elif not semantic.is_commit_action and result.allowed and result.real_side_effect_allowed is False:
                allowed += 1
        ok = checked > 0 and (paused + allowed == checked)
        return ShadowScenarioResult(
            scenario_id=scenario_id,
            status="pass" if ok else "fail",
            actions_checked=checked,
            commit_actions_paused=paused,
            non_commit_actions_allowed=allowed,
            real_side_effects=0,
            notes="shadow_acceptance_no_live_commit" if ok else "unexpected_action_policy_gap",
        ).to_dict()

    def run_default_suite(self) -> Dict[str, Any]:
        scenarios = {
            "digital_global_agent": [
                {"op_name": "read_email", "summary": "读取邮件"},
                {"op_name": "analyze_priority", "summary": "分析优先级"},
                {"op_name": "draft_reply", "summary": "生成回复草稿"},
                {"op_name": "send_reply", "summary": "对外发送回复"},
            ],
            "commerce_preparation": [
                {"op_name": "search_supplier", "summary": "查询供应商"},
                {"op_name": "prepare_cart", "summary": "准备购物车", "semantic_class": "prepare"},
                {"op_name": "checkout_order", "summary": "下单付款", "payment": True},
            ],
            "embodied_robot_mock": [
                {"op_name": "read_sensor_replay", "summary": "读取传感器回放"},
                {"op_name": "simulate_robot_move", "summary": "仿真机械臂轨迹", "semantic_class": "simulate"},
                {"op_name": "move_robot_arm", "summary": "真实移动机械臂", "physical_actuation": True},
            ],
            "contract_and_identity": [
                {"op_name": "analyze_contract", "summary": "分析合同"},
                {"op_name": "prepare_contract_summary", "summary": "生成合同摘要"},
                {"op_name": "sign_contract", "summary": "签署合同"},
                {"op_name": "represent_user", "summary": "以用户名义承诺", "semantic_class": "identity_commit"},
            ],
            "destructive_admin": [
                {"op_name": "inspect_storage", "summary": "查看存储"},
                {"op_name": "prepare_backup", "summary": "准备备份"},
                {"op_name": "delete_database", "summary": "删除数据库", "destructive": True},
            ],
        }
        results = [self.run_scenario(k, v) for k, v in scenarios.items()]
        adapter = AdapterContractGate().evaluate()
        checks = {
            "all_scenarios_pass": all(r.get("status") == "pass" for r in results),
            "scenario_count_at_least_5": len(results) >= 5,
            "no_real_side_effects": all(r.get("real_side_effects") == 0 for r in results),
            "adapter_contracts_pass": adapter.get("status") == "pass",
            "commit_actions_paused_in_every_relevant_scenario": all(r.get("commit_actions_paused", 0) >= 1 for r in results),
        }
        return {
            "status": "pass" if all(checks.values()) else "fail",
            "checks": checks,
            "results": results,
            "adapter_contract_gate": adapter,
            "invariant": "shadow_scenarios_rehearse_real_world_work_without_real_world_side_effects",
        }


def run_shadow_acceptance_suite() -> Dict[str, Any]:
    return ShadowScenarioAcceptanceSuite().run_default_suite()
