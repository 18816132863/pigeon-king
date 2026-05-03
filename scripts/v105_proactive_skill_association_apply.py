#!/usr/bin/env python3
from __future__ import annotations
import json, os, re, time
from pathlib import Path

ROOT = Path.cwd()
REPORTS = ROOT / "reports"
GOV = ROOT / "governance"
DOCS = ROOT / "docs"
for p in [REPORTS, GOV, DOCS]:
    p.mkdir(parents=True, exist_ok=True)

MATCHER = GOV / "proactive_skill_matcher.py"
RULES = DOCS / "SKILL_ACCESS_RULES.md"
MAINLINE = ROOT / "infrastructure" / "mainline_hook.py"

MATCHER_CODE = r'''#!/usr/bin/env python3
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
'''

RULES_TEXT = """# SKILL_ACCESS_RULES.md - 主动技能联想规则

## 目标

技能不能只靠用户说出关键词才触发。系统应根据用户的场景、任务、文件类型、风险、上下文主动推荐候选技能。

## 分层

1. `trigger_keywords`：被动触发词。用户明确说出时优先匹配。
2. `context_triggers`：主动场景触发。用户描述场景但没说技能名时，用它联想。
3. `proactive_scenario`：自然语言说明“什么时候应该主动推荐”。
4. `skill_policy_gate`：判断该技能是否 offline_safe / mock_only / approval_required / external_api_blocked。
5. `V90/V92/V100 commit barrier`：决定能否执行。主动推荐永远不能绕过它。

## 行为规则

- 只推荐，不自动执行。
- 每次最多推荐 3-5 个候选技能，避免打扰。
- 如果用户需求明确、当前能力明显匹配，可以主动说“这个场景适合用 X 技能”。
- 如果技能需要外部 API，而 `NO_EXTERNAL_API=true`，只能推荐 mock/dry-run 或说明被禁用。
- 如果涉及支付、签署、外发、设备、删除、身份承诺，必须标记 `approval_required`，不得自动执行。
- 用户说“不用推荐技能”后，本轮应降低推荐频率。

## 推荐话术

优先简短：

> 这个场景适合调用：A / B / C。我先按离线 dry-run 方式准备，不做真实外发。

不要每次都长篇解释。
"""

GATE_CODE = r'''#!/usr/bin/env python3
from __future__ import annotations
import json, os, importlib
from pathlib import Path

ROOT = Path.cwd()
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

def write(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def main():
    failures = []
    checks = {}
    registry = ROOT / "governance" / "skill_trigger_registry.json"
    rules = ROOT / "docs" / "SKILL_ACCESS_RULES.md"
    matcher_file = ROOT / "governance" / "proactive_skill_matcher.py"

    checks["registry_exists"] = registry.exists()
    checks["rules_exists"] = rules.exists()
    checks["matcher_exists"] = matcher_file.exists()
    for k, v in checks.items():
        if not v:
            failures.append(k)

    try:
        data = json.loads(registry.read_text(encoding="utf-8")) if registry.exists() else {}
        items = list(data.values()) if isinstance(data, dict) else data
        total = len(items)
        context_count = sum(1 for x in items if isinstance(x, dict) and x.get("context_triggers"))
        scenario_count = sum(1 for x in items if isinstance(x, dict) and x.get("proactive_scenario"))
    except Exception as e:
        total = context_count = scenario_count = 0
        failures.append(f"registry_read_error:{e}")

    try:
        m = importlib.import_module("governance.proactive_skill_matcher")
        checks["matcher_importable"] = True
        samples = {
            "json_code": m.suggest_skills("这段 JSON 报错了，帮我看看格式和字段"),
            "excel_data": m.suggest_skills("我这里有一堆表格数据，想分析一下趋势"),
            "architecture": m.suggest_skills("我在整理系统架构和模块联动，看看哪些该融合"),
            "payment_block": m.suggest_skills("帮我下单付款并发送确认邮件"),
        }
    except Exception as e:
        checks["matcher_importable"] = False
        samples = {"error": str(e)}
        failures.append("matcher_import_failed")

    checks["context_trigger_coverage_ok"] = total > 0 and context_count >= int(total * 0.8)
    checks["proactive_scenario_coverage_ok"] = total > 0 and scenario_count >= int(total * 0.8)
    if not checks["context_trigger_coverage_ok"]:
        failures.append("context_trigger_coverage_low")
    if not checks["proactive_scenario_coverage_ok"]:
        failures.append("proactive_scenario_coverage_low")

    # samples quality
    sample_ok = True
    if isinstance(samples, dict) and "error" not in samples:
        sample_ok = all(v.get("status") == "ok" for v in samples.values())
        # payment sample should be marked commit_context, not auto execution
        sample_ok = sample_ok and samples["payment_block"].get("commit_context") is True
    else:
        sample_ok = False
    checks["sample_matching_ok"] = sample_ok
    if not sample_ok:
        failures.append("sample_matching_failed")

    report = {
        "version": "V105.0",
        "status": "pass" if not failures else "partial",
        "checks": checks,
        "registry_total": total,
        "context_trigger_count": context_count,
        "proactive_scenario_count": scenario_count,
        "sample_results": samples,
        "no_external_api": os.environ.get("NO_EXTERNAL_API") == "true",
        "no_real_payment": os.environ.get("NO_REAL_PAYMENT") == "true",
        "no_real_send": os.environ.get("NO_REAL_SEND") == "true",
        "no_real_device": os.environ.get("NO_REAL_DEVICE") == "true",
        "remaining_failures": failures,
    }
    write(REPORTS / "V105_PROACTIVE_SKILL_ASSOCIATION_GATE.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
'''

def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

write(MATCHER, MATCHER_CODE)
write(RULES, RULES_TEXT)
write(ROOT / "scripts" / "v105_proactive_skill_association_gate.py", GATE_CODE)

# Patch mainline_hook lightly if present.
if MAINLINE.exists():
    s = MAINLINE.read_text(encoding="utf-8", errors="ignore")
    changed = False
    if "proactive_skill_suggestions" not in s:
        # Insert helper near top after ROOT if possible.
        helper = '''\n\ndef _v105_skill_suggestions(message=None):\n    try:\n        from governance.proactive_skill_matcher import suggest_skills\n        return suggest_skills(str(message or ""), top_k=5)\n    except Exception as e:\n        return {"status": "warning", "error": str(e), "suggestions": []}\n'''
        if "def " in s:
            idx = s.find("def ")
            s = s[:idx] + helper + "\n" + s[idx:]
        else:
            s += helper
        # Add field before return payload in common patterns.
        # Conservative: if payload dict exists, add assignment before return.
        s = s.replace("return payload", "payload['proactive_skill_suggestions'] = _v105_skill_suggestions(message or goal if 'goal' in globals() else message)\n    return payload")
        s = s.replace("return result", "result['proactive_skill_suggestions'] = _v105_skill_suggestions(message if 'message' in locals() else None)\n    return result")
        changed = True
    if changed:
        MAINLINE.write_text(s, encoding="utf-8")

# Patch AGENTS/TOOLS with short rule if present.
for fname in ["AGENTS.md", "TOOLS.md"]:
    p = ROOT / fname
    if p.exists():
        s = p.read_text(encoding="utf-8", errors="ignore")
        marker = "V105 Proactive Skill Association"
        if marker not in s:
            s += f"""

## {marker}
- 根据用户当前场景主动联想技能，不只等用户说出触发关键词。
- 主动技能联想只推荐候选，不自动执行。
- 外部 API、外发、支付、签署、设备、删除类动作仍必须走 V90/V92/V100 网关。
- 规则详见 docs/SKILL_ACCESS_RULES.md。
"""
            p.write_text(s, encoding="utf-8")

report = {
    "version": "V105.0",
    "status": "pass",
    "created": [str(MATCHER.relative_to(ROOT)), str(RULES.relative_to(ROOT)), "scripts/v105_proactive_skill_association_gate.py"],
    "mainline_hook_patched": MAINLINE.exists(),
    "no_external_api": os.environ.get("NO_EXTERNAL_API") == "true",
    "note": "主动技能联想只推荐，不执行；执行仍归 V90/V92/V100 网关。",
}
(REPORTS / "V105_PROACTIVE_SKILL_ASSOCIATION_APPLY.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
