# -*- coding: utf-8 -*-
"""V86 goal compiler.

Turns one natural-language request into GoalSpec: objective, constraints,
information sources, risk hints, approval points, success criteria and subgoals.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from .schemas import GoalSpec


class GoalCompiler:
    NEGATIVE_CONSTRAINT_WORDS = ("不要", "不能", "别", "禁止", "不要一步步", "不要反复", "不要问")
    URGENT_WORDS = ("马上", "立刻", "现在", "紧急", "直接", "一次性", "不要一点点")

    RISK_WORDS = {
        "external_send": ("发送", "发给", "邮件", "短信", "微信", "发布", "群发", "提交"),
        "money": ("付款", "支付", "转账", "购买", "下单", "提现", "扣费"),
        "delete": ("删除", "清空", "覆盖", "销毁", "移除", "永久"),
        "install_code": ("安装", "pip install", "npm install", "下载执行", "插件", "依赖"),
        "privacy": ("身份证", "密码", "token", "密钥", "客户资料", "隐私", "账号"),
        "system_change": ("系统改写", "主流程", "覆盖包", "根目录", "重构", "架构迁移"),
    }

    SOURCE_WORDS = {
        "email": ("邮件", "邮箱", "email"),
        "calendar": ("日程", "会议", "calendar", "提醒"),
        "files": ("文件", "文档", "pdf", "docx", "zip", "压缩包", "源码", "工作区"),
        "web_or_knowledge": ("最新", "现在", "搜索", "官网", "查", "政策", "规则", "价格"),
        "device": ("手机", "设备", "相册", "联系人", "闹钟", "短信"),
        "model_router": ("模型", "api", "大模型", "路由", "决策引擎"),
    }

    CAPABILITY_WORDS = {
        "code_patch": ("代码", "修复", "补丁", "压缩包", "覆盖", "脚本", "测试"),
        "business_planning": ("方案", "策略", "计划", "电商", "直播", "团长"),
        "document_analysis": ("文档", "论文", "pdf", "报告"),
        "visual_analysis": ("截图", "图片", "报错图", "页面"),
        "generation": ("生成", "做一个", "画", "视频", "头像", "海报"),
    }

    def compile(self, request: str, context: Dict[str, Any] | None = None) -> GoalSpec:
        context = context or {}
        if not isinstance(request, str) or not request.strip():
            raise ValueError("request must be a non-empty string")

        raw = " ".join(request.strip().split())
        objective = self._normalize_objective(raw)
        risk_hints = self._extract_risk_hints(raw)
        approval_points = self._approval_points(risk_hints)
        info_sources = self._information_sources(raw)
        objectives = self._split_objectives(objective)
        constraints = self._constraints(raw, context)

        return GoalSpec(
            goal_id=GoalSpec.new_id(raw),
            raw_request=raw,
            objective=objective,
            objectives=objectives,
            constraints=constraints,
            success_criteria=self._success_criteria(raw, risk_hints),
            information_sources=info_sources,
            risk_hints=risk_hints,
            approval_points=approval_points,
            time_scope=self._time_scope(raw, context),
            priority=self._priority(raw, risk_hints),
            autonomy_mode=context.get("autonomy_mode", "bounded_autonomy"),
        )

    def _normalize_objective(self, text: str) -> str:
        return re.sub(r"^(帮我|给我|请|麻烦|现在|直接)\s*", "", text).strip("。.!！ ")

    def _split_objectives(self, objective: str) -> List[Dict[str, Any]]:
        parts = [p.strip(" 。.!！?？") for p in re.split(r"，|,|；|;|然后|再|并且|以及|同时|and|then", objective) if p.strip(" 。.!！?？")]
        if not parts:
            parts = [objective]
        result = []
        for i, part in enumerate(parts[:12], 1):
            result.append({
                "objective_id": f"obj_{i}",
                "title": part,
                "depends_on": [] if i == 1 else [f"obj_{i-1}"],
                "required_capabilities": self._infer_capabilities(part),
            })
        return result

    def _infer_capabilities(self, text: str) -> List[str]:
        caps = ["goal_understanding", "policy_judgement", "task_graph"]
        lower = text.lower()
        for cap, words in self.CAPABILITY_WORDS.items():
            if any(w.lower() in lower for w in words):
                caps.append(cap)
        return list(dict.fromkeys(caps))

    def _extract_risk_hints(self, text: str) -> List[str]:
        lower = text.lower()
        risks = []
        for name, words in self.RISK_WORDS.items():
            if any(w.lower() in lower for w in words):
                risks.append(name)
        return risks or ["low"]

    def _approval_points(self, risk_hints: List[str]) -> List[str]:
        mapping = {
            "external_send": "before_external_send_or_publish",
            "money": "before_payment_or_purchase",
            "delete": "before_destructive_delete_or_overwrite",
            "install_code": "before_new_code_or_dependency_install",
            "privacy": "before_private_data_export",
            "system_change": "before_system_wide_overwrite",
        }
        return [mapping[r] for r in risk_hints if r in mapping]

    def _information_sources(self, text: str) -> List[str]:
        lower = text.lower()
        sources = []
        for source, words in self.SOURCE_WORDS.items():
            if any(w.lower() in lower for w in words):
                sources.append(source)
        return sources or ["conversation_context"]

    def _constraints(self, text: str, context: Dict[str, Any]) -> List[str]:
        constraints = [
            "preserve_existing_behavior",
            "audit_side_effects",
            "prefer_one_shot_solution",
            "do_not_install_untrusted_code_without_approval",
        ]
        if any(w in text for w in self.NEGATIVE_CONSTRAINT_WORDS):
            constraints.append("minimize_repeated_followups")
        if "直接" in text or "一次性" in text:
            constraints.append("complete_as_much_as_possible_in_one_pass")
        if context.get("no_external"):
            constraints.append("no_external_connectors")
        if context.get("preserve_data", True):
            constraints.append("do_not_destroy_user_data")
        return list(dict.fromkeys(constraints))

    def _success_criteria(self, text: str, risk_hints: List[str]) -> List[str]:
        criteria = [
            "goal_spec_created",
            "task_graph_created",
            "policy_judgement_applied",
            "execution_plan_created",
            "safe_nodes_prepared_or_executed",
            "result_verified",
            "experience_written_back",
        ]
        if risk_hints and risk_hints != ["low"]:
            criteria.append("high_risk_nodes_blocked_for_approval")
        return criteria

    def _time_scope(self, text: str, context: Dict[str, Any]) -> str:
        if context.get("time_scope"):
            return str(context["time_scope"])
        for label, words in {
            "immediate": ("马上", "立刻", "现在", "直接"),
            "today": ("今天", "今日"),
            "tomorrow": ("明天",),
            "this_week": ("这周", "本周"),
            "next_week": ("下周",),
            "this_month": ("本月", "这个月"),
        }.items():
            if any(w in text for w in words):
                return label
        return "unspecified"

    def _priority(self, text: str, risk_hints: List[str]) -> str:
        if any(w in text for w in self.URGENT_WORDS):
            return "high"
        if any(r in risk_hints for r in ("money", "delete", "install_code", "privacy", "system_change")):
            return "controlled"
        return "normal"
