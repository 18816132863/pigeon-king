#!/usr/bin/env python3
"""
V105 Proactive Skill Matcher

主动技能联想器：根据用户上下文、场景、意图和已有 skill_trigger_registry.json
中的 context_triggers / proactive_scenario，为当前对话推荐候选技能。

边界：
- 只做推荐，不直接执行技能。
- NO_EXTERNAL_API=true 时，需要外部 API 的技能降级为 blocked / mock_only。
- commit 类动作仍由 V90/V92/V100 runtime gate / commit barrier 处理。
"""
from __future__ import annotations
import json, os, re, time
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "governance" / "skill_trigger_registry.json"
AUDIT = ROOT / "governance" / "audit" / "proactive_skill_matcher.jsonl"

COMMIT_TERMS = [
    "支付", "付款", "转账", "下单", "购买", "签署", "签合同", "发送", "群发", "公开发布",
    "发邮件", "发短信", "webhook", "飞书", "企业微信", "控制设备", "开门", "关机", "删除", "清空",
    "payment", "pay", "transfer", "sign", "send", "post", "publish", "device", "delete", "remove"
]

DOMAIN_HINTS = {
    "spreadsheet": ["表格", "excel", "xlsx", "csv", "数据表", "透视", "统计", "一堆数据"],
    "document": ["pdf", "docx", "文档", "论文", "报告", "格式", "排版", "转换"],
    "image": ["图片", "图像", "logo", "头像", "海报", "商品图", "插画", "画图", "视觉"],
    "video": ["视频", "短视频", "分镜", "脚本", "直播", "口播", "剪辑"],
    "code": ["代码", "报错", "python", "json", "接口", "模块", "导入", "bug", "脚本", "架构"],
    "memory": ["记住", "记录", "下次", "偏好", "人格", "上下文", "记忆", "不要忘"],
    "finance": ["股票", "行情", "财报", "基金", "交易", "市场", "量化"],
    "search": ["查", "搜索", "找", "调研", "资料", "信息", "新闻"],
    "automation": ["自动", "流程", "批量", "工作流", "一键", "定时", "任务"],
    "safety": ["密码", "token", "api key", "密钥", "泄露", "权限", "安全", "风控"],
}

CATEGORY_HINTS = {
    "spreadsheet": ["excel", "xlsx", "table", "csv", "data"],
    "document": ["pdf", "doc", "docx", "ppt", "report", "writing"],
    "image": ["image", "picture", "art", "design", "visual"],
    "video": ["video", "script", "remotion"],
    "code": ["json", "regex", "code", "developer", "webapp"],
    "memory": ["brain", "memory", "2nd-brain", "note"],
    "finance": ["stock", "finance", "trading", "quote", "eastmoney"],
    "search": ["search", "news", "arxiv", "web", "browser"],
    "automation": ["agent", "automation", "task", "workflow", "calendar", "email"],
    "safety": ["env", "guard", "secret", "security"],
}

def _safe_load_registry() -> Dict[str, Dict[str, Any]]:
    if not REGISTRY.exists():
        return {}
    try:
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): v for k, v in data.items() if isinstance(v, dict)}
        if isinstance(data, list):
            return {str(x.get("name") or x.get("skill_id") or i): x for i, x in enumerate(data) if isinstance(x, dict)}
    except Exception:
        return {}
    return {}

def _text_blob(skill: Dict[str, Any]) -> str:
    vals = []
    for key in ["name", "description", "category", "trigger_scenarios", "proactive_scenario"]:
        vals.append(str(skill.get(key, "")))
    for key in ["trigger_keywords", "context_triggers"]:
        v = skill.get(key, [])
        if isinstance(v, list):
            vals.extend(map(str, v))
        else:
            vals.append(str(v))
    return "\n".join(vals).lower()

def infer_domains(message: str) -> List[str]:
    m = (message or "").lower()
    domains = []
    for domain, hints in DOMAIN_HINTS.items():
        if any(h.lower() in m for h in hints):
            domains.append(domain)
    return domains

def is_commit_like(message: str) -> bool:
    m = (message or "").lower()
    return any(t.lower() in m for t in COMMIT_TERMS)

def score_skill(skill: Dict[str, Any], message: str, domains: List[str]) -> Dict[str, Any]:
    m = (message or "").lower()
    blob = _text_blob(skill)
    score = 0
    reasons = []

    # context trigger match
    ctx = skill.get("context_triggers", [])
    if isinstance(ctx, list):
        for c in ctx:
            c = str(c).strip().lower()
            if not c:
                continue
            # tokenize Chinese/English lightly by substring and keyword overlap
            parts = [x for x in re.split(r"[\s,，、/|;；：:]+", c) if x]
            hit = 0
            for part in parts:
                if len(part) >= 2 and part in m:
                    hit += 1
            if c in m or hit >= 1:
                score += 8 + min(hit, 4)
                reasons.append("context_trigger")
                break

    # passive keyword match still useful
    for kw in skill.get("trigger_keywords", []) or []:
        kw = str(kw).strip().lower()
        if kw and kw in m:
            score += 10
            reasons.append("keyword")
            break

    # domain match
    for d in domains:
        hints = CATEGORY_HINTS.get(d, [])
        if any(h in blob for h in hints):
            score += 5
            reasons.append(f"domain:{d}")

    # description/proactive scenario overlap
    words = [w for w in re.split(r"[\s,，、/|;；：:。.!?？]+", m) if len(w) >= 2]
    overlap = 0
    for w in words[:30]:
        if w in blob:
            overlap += 1
    if overlap:
        score += min(overlap, 6)
        reasons.append("description_overlap")

    # external API safety
    blocked = False
    if os.environ.get("NO_EXTERNAL_API") == "true" and skill.get("requires_external_api"):
        blocked = True
        score = max(0, score - 8)
        reasons.append("external_api_blocked")

    # commit class cannot auto-execute
    approval_required = False
    if is_commit_like(message):
        approval_required = True
        reasons.append("commit_context_requires_approval")

    return {
        "name": skill.get("name") or skill.get("skill_id") or "unknown",
        "score": score,
        "reasons": sorted(set(reasons)),
        "category": skill.get("category", "general"),
        "requires_external_api": bool(skill.get("requires_external_api")),
        "blocked_by_offline_policy": blocked,
        "approval_required": approval_required,
        "proactive_scenario": skill.get("proactive_scenario", ""),
        "context_triggers": skill.get("context_triggers", []),
    }

def suggest_skills(message: str, *, top_k: int = 5, min_score: int = 4, include_blocked: bool = False) -> Dict[str, Any]:
    registry = _safe_load_registry()
    domains = infer_domains(message)
    rows = []
    for skill in registry.values():
        row = score_skill(skill, message, domains)
        if row["score"] >= min_score and (include_blocked or not row["blocked_by_offline_policy"]):
            rows.append(row)
    rows.sort(key=lambda x: x["score"], reverse=True)
    suggestions = rows[:top_k]
    result = {
        "status": "ok",
        "mode": "proactive_skill_suggestion",
        "message": message,
        "domains": domains,
        "suggestions": suggestions,
        "suggestion_count": len(suggestions),
        "commit_context": is_commit_like(message),
        "no_external_api": os.environ.get("NO_EXTERNAL_API") == "true",
        "real_execution": False,
        "note": "仅推荐候选技能，不自动执行。高风险/外部能力必须走 V90/V92/V100 网关。",
    }
    write_audit(result)
    return result

def write_audit(payload: Dict[str, Any]) -> None:
    try:
        AUDIT.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass

class ProactiveSkillMatcher:
    def suggest(self, message: str, top_k: int = 5) -> Dict[str, Any]:
        return suggest_skills(message, top_k=top_k)
