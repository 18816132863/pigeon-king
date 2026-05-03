from __future__ import annotations
from .schemas import GoalContract, GoalNode, RiskLevel, new_id

class GoalStrategyKernel:
    """Goal-strategy kernel: converts one user message into an executable goal contract."""

    def compile(self, raw_input: str) -> GoalContract:
        text = raw_input.strip()
        lower = text.lower()

        sensitive = any(x in lower for x in ["token", "secret", "api_key", "password"]) or any(x in text for x in ["密钥", "密码"])
        irreversible = any(x in text for x in ["删除", "清空", "转账", "付款", "支付", "安装未知"])
        external = any(x in text for x in ["发送", "发给", "群发", "客户", "外部"])
        write = any(x in text for x in ["覆盖", "替换", "压缩包", "写入", "保存", "修改"])
        research = any(x in text for x in ["查", "找", "检索", "邮件", "日程", "报告", "总结"])
        large_batch = any(x in text for x in ["一次性", "全部", "最终", "整的", "直接替换", "不要一点点"])

        if sensitive:
            risk = RiskLevel.L4_SENSITIVE_OR_IRREVERSIBLE
        elif irreversible:
            risk = RiskLevel.L4_SENSITIVE_OR_IRREVERSIBLE
        elif external:
            risk = RiskLevel.L3_EXTERNAL_SIDE_EFFECT
        elif write:
            risk = RiskLevel.L2_REVERSIBLE
        elif research:
            risk = RiskLevel.L1_LOW
        else:
            risk = RiskLevel.L1_LOW

        constraints = []
        if large_batch:
            constraints += ["one_shot_complete_package", "avoid_incremental_patch", "include_single_command"]
        if write:
            constraints += ["must_include_verification_script", "must_include_rollback_plan"]
        if external or irreversible or sensitive:
            constraints += ["must_pass_constitution_judge", "approval_before_side_effect"]
        if any(x in text for x in ["缺技能", "缺能力", "新能力", "沙箱", "评测", "灰度", "上线", "安装技能", "扩展能力"]):
            constraints += ["capability_gap_must_be_explicit", "sandbox_before_capability_promotion", "feature_flag_and_rollback_required"]

        info_sources = ["user_input", "project_memory", "procedure_memory"]
        if research:
            info_sources += ["connected_sources_or_web_if_available"]
        if "邮件" in text:
            info_sources.append("gmail_connector_if_enabled")
        if "日程" in text:
            info_sources.append("calendar_connector_if_enabled")
        if "压缩包" in text or "版本" in text or "覆盖" in text:
            info_sources += ["workspace_files", "release_reports", "verification_scripts"]

        nodes = [
            GoalNode(new_id("goalnode"), "理解真实目标", 100, "目标、约束、边界被明确写入 GoalContract", constraints),
            GoalNode(new_id("goalnode"), "生成任务图并区分自动/审批", 90, "得到 DAG、checkpoint、审批节点和恢复策略", constraints),
            GoalNode(new_id("goalnode"), "安全执行或安全预演", 80, "低风险自动完成，高风险等待审批，敏感内容阻断", constraints),
            GoalNode(new_id("goalnode"), "输出验收结果并回写记忆", 70, "输出完成报告、失败恢复、记忆写入记录", constraints),
        ]

        approval_required = risk in {RiskLevel.L3_EXTERNAL_SIDE_EFFECT, RiskLevel.L4_SENSITIVE_OR_IRREVERSIBLE}
        blocked = sensitive and any(x in text for x in ["发", "发送", "发给", "群发", "导出"])

        if blocked:
            automation_boundary = "blocked: sensitive credential exfiltration is not executable"
        elif approval_required:
            automation_boundary = "dry-run automatically; real side effect waits for approval"
        else:
            automation_boundary = "safe to execute in controlled local/dry-run mode"

        completion_definition = "输出目标树、任务图、信息源、风险分类、自动执行部分、审批部分、checkpoint、执行结果、失败恢复和记忆回写记录"

        return GoalContract(
            id=new_id("goal"),
            raw_input=text,
            objective=text,
            goal_tree=nodes,
            constraints=constraints,
            non_goals=["do not fabricate execution", "do not perform unapproved side effects", "do not leak secrets"],
            risk_level=risk,
            automation_boundary=automation_boundary,
            approval_required=approval_required,
            blocked=blocked,
            completion_definition=completion_definition,
            information_sources=list(dict.fromkeys(info_sources)),
        )
