from __future__ import annotations
from .schemas import GoalContract, JudgeDecision, RiskLevel

class ConstitutionJudge:
    """Hard constitution + soft preference + contextual judge."""

    def judge(self, contract: GoalContract) -> tuple[JudgeDecision, list[str]]:
        reasons = []
        raw = contract.raw_input
        lower = raw.lower()

        if any(x in lower for x in ["api_key", "secret", "token", "password"]) and any(x in raw for x in ["发", "发送", "发给", "群发", "导出"]):
            return JudgeDecision.BLOCK, ["block_secret_exfiltration"]

        if any(x in raw for x in ["密钥", "密码"]) and any(x in raw for x in ["发", "发送", "发给", "群发", "导出"]):
            return JudgeDecision.BLOCK, ["block_sensitive_credential_exfiltration"]

        if contract.risk_level == RiskLevel.L4_SENSITIVE_OR_IRREVERSIBLE:
            reasons.append("L4 action requires explicit approval or remains dry-run")
            return JudgeDecision.APPROVAL_REQUIRED, reasons

        if contract.risk_level == RiskLevel.L3_EXTERNAL_SIDE_EFFECT:
            reasons.append("external side effect requires approval")
            return JudgeDecision.APPROVAL_REQUIRED, reasons

        if "one_shot_complete_package" in contract.constraints:
            reasons.append("respect user preference: complete package + one command")
        return JudgeDecision.ALLOW, reasons
