from __future__ import annotations
from .schemas import ToolMode

class ToolExecutionPolicy:
    """Maps task/risk/tool into real/dry_run/approval_required/blocked."""

    HIGH_RISK = {"L3_external_side_effect", "L4_sensitive_or_irreversible"}
    DANGEROUS_KINDS = {"approval_gate", "mail_operation", "calendar_operation", "device_operation", "action_bridge", "script_operation"}
    SECRET_WORDS = ("token", "api_key", "secret", "password", "密钥", "密码")

    def choose_mode(self, ai_result, task, tool_spec: dict) -> tuple[ToolMode, str]:
        raw = ai_result.raw_input
        lower = raw.lower()

        if any(word in lower for word in self.SECRET_WORDS[:4]) or any(word in raw for word in self.SECRET_WORDS[4:]):
            if any(x in raw for x in ["发", "发送", "发给", "群发", "导出"]):
                return ToolMode.BLOCKED, "secret or credential exfiltration is blocked"

        if getattr(task, "status").value == "blocked":
            return ToolMode.BLOCKED, "task blocked by AIShapeCore constitution judge"

        if getattr(task, "requires_approval", False):
            return ToolMode.APPROVAL_REQUIRED, "task requires human approval before real side effect"

        if task.kind in self.DANGEROUS_KINDS or ai_result.risk_level.value in self.HIGH_RISK:
            return ToolMode.APPROVAL_REQUIRED, "high-risk or external tool requires approval"

        if bool(tool_spec.get("safe_real")):
            return ToolMode.REAL, "safe local/internal tool can run in real mode"

        return ToolMode.DRY_RUN, "tool is bound but defaults to dry-run"
