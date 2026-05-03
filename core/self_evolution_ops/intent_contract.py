from __future__ import annotations

from typing import List
from .schemas import IntentContract, ContractStatus, new_id


class IntentContractCompiler:
    """V107: turns a raw goal into an executable contract."""

    def compile(self, goal: str) -> IntentContract:
        constraints: List[str] = []
        risk_notes: List[str] = []
        non_goals: List[str] = ["do not perform irreversible external actions without approval"]

        if any(x in goal for x in ["直接", "一次性", "不要一点点"]):
            constraints.append("prefer one-shot complete package over incremental patching")
        if any(x in goal for x in ["压缩包", "覆盖包", "命令"]):
            constraints.append("deliver artifact package and one command")
        if any(x in goal for x in ["发送", "转账", "删除", "安装未知", "密钥", "token"]):
            risk_notes.append("contains high-risk or sensitive operation")
        if any(x in goal for x in ["不确定", "随便", "可能"]):
            status = ContractStatus.NEEDS_CLARIFICATION
        elif any(x in goal for x in ["导出密钥", "token 发到", "密码发给"]):
            status = ContractStatus.UNSAFE
        else:
            status = ContractStatus.READY

        acceptance = [
            "goal is decomposed into verifiable deliverables",
            "risk boundary is explicit",
            "result has a deterministic verification command or report",
        ]
        if "压缩包" in goal or "覆盖包" in goal:
            acceptance.append("artifact package is generated and ready to apply")

        return IntentContract(
            id=new_id("contract"),
            goal=goal,
            objective=goal.strip(),
            acceptance_criteria=acceptance,
            constraints=constraints,
            non_goals=non_goals,
            risk_notes=risk_notes,
            status=status,
        )
