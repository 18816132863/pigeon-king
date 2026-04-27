"""V26.0 Operating Contract V3.

Purpose:
- Convert a one-sentence user goal into a governed operating contract.
- Keep this layer in L1 Core as pure data and deterministic normalization.
- It does not execute tools, judge risk, or write memory.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import hashlib
import json


@dataclass(frozen=True)
class Objective:
    name: str
    description: str
    priority: int = 50
    deadline: Optional[str] = None
    done_definition: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class Constraint:
    kind: str
    value: str
    hard: bool = True


@dataclass(frozen=True)
class ApprovalPoint:
    action_kind: str
    reason: str
    required: bool = True


@dataclass(frozen=True)
class OperatingContract:
    contract_id: str
    raw_goal: str
    objectives: List[Objective]
    constraints: List[Constraint]
    risk_boundary: str
    information_sources: List[str]
    approval_points: List[ApprovalPoint]
    created_at: str
    owner: str = "user"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def requires_approval_for(self, action_kind: str) -> bool:
        return any(p.required and p.action_kind == action_kind for p in self.approval_points)


class GoalContractCompilerV3:
    """Deterministic baseline compiler.

    This is intentionally rule-based so smoke tests are stable.
    A production caller may feed LLM-parsed fields into the same contract type.
    """

    destructive_keywords = ("删除", "清空", "转账", "支付", "发送给别人", "导出隐私", "安装未知")
    device_keywords = ("提醒", "闹钟", "日程", "通知", "打开", "设置", "文件", "截图")
    memory_keywords = ("记住", "以后", "习惯", "偏好", "每次")

    def compile(self, raw_goal: str, *, owner: str = "user") -> OperatingContract:
        normalized = " ".join(raw_goal.strip().split())
        if not normalized:
            raise ValueError("raw_goal is empty")

        risk = "L1"
        approvals: List[ApprovalPoint] = []
        constraints: List[Constraint] = [
            Constraint("architecture", "six_layer_only_no_L7", True),
            Constraint("device_execution", "global_serial_for_multi_device_actions", True),
            Constraint("state", "durable_state_required", True),
        ]

        if any(k in normalized for k in self.destructive_keywords):
            risk = "L4"
            approvals.append(ApprovalPoint("destructive_action", "涉及破坏性/支付/隐私动作，必须强确认"))
        elif any(k in normalized for k in self.device_keywords):
            risk = "L2"
            approvals.append(ApprovalPoint("device_side_effect", "端侧副作用动作需要可验证回执或 pending_verify"))
        if any(k in normalized for k in self.memory_keywords):
            approvals.append(ApprovalPoint("long_term_memory_write", "长期记忆写入必须经过记忆守卫"))

        objective = Objective(
            name=self._infer_name(normalized),
            description=normalized,
            priority=80 if "现在" in normalized or "立即" in normalized else 50,
            done_definition=[
                "目标被拆成任务图",
                "高风险动作经过裁判",
                "端侧动作串行执行并核验",
                "结果和经验按守卫规则写回",
            ],
        )
        contract_id = self._make_id(normalized, owner)
        return OperatingContract(
            contract_id=contract_id,
            raw_goal=normalized,
            objectives=[objective],
            constraints=constraints,
            risk_boundary=risk,
            information_sources=self._infer_sources(normalized),
            approval_points=approvals,
            created_at=datetime.now(timezone.utc).isoformat(),
            owner=owner,
        )

    def _infer_name(self, goal: str) -> str:
        if "提醒" in goal or "闹钟" in goal:
            return "device_reminder_goal"
        if "整理" in goal or "计划" in goal:
            return "planning_goal"
        if "安装" in goal or "技能" in goal or "能力" in goal:
            return "capability_extension_goal"
        return "general_operating_goal"

    def _infer_sources(self, goal: str) -> List[str]:
        sources = ["conversation_context"]
        if any(k in goal for k in ("文件", "文档", "资料")):
            sources.append("file_library")
        if any(k in goal for k in ("端侧", "手机", "闹钟", "提醒", "日程")):
            sources.append("device_capability_bus")
        if any(k in goal for k in ("网页", "外部", "接口", "connector", "MCP")):
            sources.append("world_interface")
        return sources

    def _make_id(self, goal: str, owner: str) -> str:
        payload = json.dumps({"goal": goal, "owner": owner}, ensure_ascii=False, sort_keys=True)
        return "goal_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
