from __future__ import annotations

from pathlib import Path
from typing import Dict, List
import re

from .schemas import (
    ConstitutionRule,
    ConstitutionDecision,
    RuleSeverity,
    DecisionStatus,
    PermissionScope,
    new_id,
    dataclass_to_dict,
)
from .storage import JsonStore


class ConstitutionKernel:
    """V97: Personal constitution and lawbook.

    This is the hard boundary layer above autonomy. It converts action text into
    allow / approval / block decisions.
    """

    def __init__(self, root: str | Path = ".operating_agent_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "constitution_rules.json")
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if self.store.read([]):
            return
        rules = [
            ConstitutionRule(new_id("rule"), "block_payment_without_explicit_approval", r"转账|付款|支付|打款|收款账户", RuleSeverity.APPROVAL_REQUIRED, "Money movement requires explicit approval.", tags=["money", "approval"]),
            ConstitutionRule(new_id("rule"), "block_delete_or_overwrite", r"删除|清空|覆盖全部|格式化|永久移除", RuleSeverity.APPROVAL_REQUIRED, "Irreversible destructive operations require approval.", tags=["destructive"]),
            ConstitutionRule(new_id("rule"), "block_secret_export", r"(导出|发送|发到|发给|群发|外部发送).*(密钥|密码|token|secret|隐私)|(密钥|密码|token|secret|隐私).*(发送|发到|发给|群发|外部发送)", RuleSeverity.BLOCK, "Secrets and sensitive data must not be exported.", tags=["secret", "privacy"]),
            ConstitutionRule(new_id("rule"), "approval_external_send", r"发给客户|发送邮件|群发|外部发送|发到群里|提交给平台", RuleSeverity.APPROVAL_REQUIRED, "External side effects require human approval.", tags=["external"]),
            ConstitutionRule(new_id("rule"), "approval_unknown_install", r"安装未知|自动安装|pip install|下载执行|运行陌生代码", RuleSeverity.APPROVAL_REQUIRED, "Unknown code installation requires sandbox evaluation and approval.", tags=["install"]),
            ConstitutionRule(new_id("rule"), "warn_low_risk_plan", r"计划|整理|总结|检查|生成方案", RuleSeverity.INFO, "Low-risk planning action.", tags=["low_risk"]),
        ]
        self.store.write([dataclass_to_dict(x) for x in rules])

    def list_rules(self) -> List[ConstitutionRule]:
        return [self._from_dict(x) for x in self.store.read([])]

    def add_rule(self, name: str, pattern: str, severity: RuleSeverity, reason: str, tags: List[str] | None = None) -> ConstitutionRule:
        data = self.store.read([])
        rule = ConstitutionRule(new_id("rule"), name, pattern, severity, reason, tags=tags or [])
        data.append(dataclass_to_dict(rule))
        self.store.write(data)
        return rule

    def evaluate(self, action_summary: str) -> ConstitutionDecision:
        matched: List[ConstitutionRule] = []
        for rule in self.list_rules():
            if not rule.enabled:
                continue
            if re.search(rule.pattern, action_summary, flags=re.I):
                matched.append(rule)

        required: List[PermissionScope] = []
        if re.search(r"转账|付款|支付|打款", action_summary):
            required.append(PermissionScope.PAYMENT)
        if re.search(r"发送邮件|发给客户|外部发送|群发|提交给平台", action_summary):
            required.append(PermissionScope.EXTERNAL_SEND)
        if re.search(r"安装|pip install|下载执行", action_summary):
            required.append(PermissionScope.INSTALL)
        if re.search(r"密钥|密码|token|secret|隐私", action_summary, flags=re.I):
            required.append(PermissionScope.SECRET_ACCESS)

        if any(r.severity == RuleSeverity.BLOCK for r in matched):
            return ConstitutionDecision(
                status=DecisionStatus.BLOCK,
                matched_rules=[r.name for r in matched],
                reason="Blocked by hard constitution rule.",
                required_permissions=required,
            )

        if any(r.severity == RuleSeverity.APPROVAL_REQUIRED for r in matched) or required:
            return ConstitutionDecision(
                status=DecisionStatus.APPROVAL_REQUIRED,
                matched_rules=[r.name for r in matched],
                reason="Approval required by constitution.",
                required_permissions=required,
            )

        return ConstitutionDecision(
            status=DecisionStatus.ALLOW,
            matched_rules=[r.name for r in matched],
            reason="Allowed by constitution.",
            required_permissions=required,
        )

    def _from_dict(self, item: Dict) -> ConstitutionRule:
        return ConstitutionRule(
            id=item["id"],
            name=item["name"],
            pattern=item["pattern"],
            severity=RuleSeverity(item["severity"]),
            reason=item["reason"],
            enabled=bool(item.get("enabled", True)),
            tags=list(item.get("tags", [])),
        )
