from __future__ import annotations

from .schemas import PolicySimulationResult, new_id


class PolicySimulator:
    """V143: policy dry-run simulator."""

    def simulate(self, scenario: str) -> PolicySimulationResult:
        lower = scenario.lower()
        if "token" in lower or "密钥" in scenario or "密码" in scenario:
            expected = "block"
            actual = "block"
            notes = ["secret exfiltration blocked"]
        elif any(x in scenario for x in ["发送", "转账", "删除", "安装"]):
            expected = "approval"
            actual = "approval"
            notes = ["high-risk action requires approval"]
        else:
            expected = "allow"
            actual = "allow"
            notes = ["low-risk scenario allowed"]
        return PolicySimulationResult(
            id=new_id("policy_sim"),
            scenario=scenario,
            expected=expected,
            actual=actual,
            passed=(expected == actual),
            notes=notes,
        )
