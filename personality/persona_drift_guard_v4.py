"""V34.0 Persona Drift Guard V4.

Keeps the agent persona stable:
- Direct, one-step deliverables for this user.
- Six-layer architecture discipline.
- No uncontrolled autonomy.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class PersonaRule:
    name: str
    instruction: str
    severity: str = "medium"

    def to_dict(self):
        return asdict(self)


class PersonaDriftGuardV4:
    def __init__(self):
        self.rules = [
            PersonaRule("direct_delivery", "优先给可执行包、命令和验收标准，不要来回追问。", "high"),
            PersonaRule("six_layer_discipline", "agent_kernel 属于 L3，不允许新增 L7。", "high"),
            PersonaRule("safe_autonomy", "自治必须经过规则、审计、审批、回滚边界。", "high"),
            PersonaRule("state_first", "长任务必须先写状态，再推进。", "medium"),
        ]

    def check_response_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        violations: List[str] = []
        if plan.get("creates_L7"):
            violations.append("six_layer_discipline")
        if plan.get("high_risk_auto_execute_without_approval"):
            violations.append("safe_autonomy")
        if plan.get("long_task_without_state"):
            violations.append("state_first")
        if plan.get("asks_unnecessary_clarification"):
            violations.append("direct_delivery")
        return {"pass": not violations, "violations": violations, "rules": [r.to_dict() for r in self.rules]}
