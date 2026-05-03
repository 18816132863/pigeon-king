#!/usr/bin/env python3
"""
技能规则化引擎 — 技能新增自动注册、触发词生成、条件定义

每次新增技能时，此模块自动：
1. 扫描 skills/ 目录下所有未注册的 SKILL.md
2. 从 SKILL.md 提取触发词、场景描述、API 依赖
3. 自动生成高质量触发关键词
4. 自动推演触发条件（什么场景下该技能被唤醒）
5. 写入 governance/skill_trigger_registry.json

用法：
  自动检测并注册所有新技能：
    python3 -c "from core.skill_rules_engine import auto_register_new_skills; auto_register_new_skills()"
  
  手动注册单个技能：
    python3 -c "from core.skill_rules_engine import register_skill; register_skill('my-skill')"
  
  查看已注册技能信息：
    python3 -c "from core.skill_rules_engine import get_skill_info; print(get_skill_info('weather'))"
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Set

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
REGISTRY_FILE = ROOT / "governance" / "skill_trigger_registry.json"


# ════════════════════════════════════════════════════════════════
# 技能触发定义结构
# ════════════════════════════════════════════════════════════════

_TRIGGER_REGISTRY: Dict[str, Dict[str, Any]] = {}


def _load_registry() -> Dict[str, Any]:
    """从文件加载当前注册表。"""
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_registry() -> None:
    """保存当前注册表到文件。"""
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(_TRIGGER_REGISTRY, f, ensure_ascii=False, indent=2)


def register(
    name: str,
    *,
    trigger_keywords: List[str] = None,
    trigger_scenarios: str = "",
    requires_external_api: bool = False,
    requires_env_vars: List[str] = None,
    requires_bins: List[str] = None,
    category: str = "general",
    description: str = "",
    is_system_skill: bool = False,
    auto_trigger_cron: str = "",
) -> None:
    """注册一个技能的触发定义。"""
    _TRIGGER_REGISTRY[name] = {
        "name": name,
        "trigger_keywords": trigger_keywords or [],
        "trigger_scenarios": trigger_scenarios,
        "requires_external_api": requires_external_api,
        "requires_env_vars": requires_env_vars or [],
        "requires_bins": requires_bins or [],
        "category": category,
        "description": description,
        "is_system_skill": is_system_skill,
        "auto_trigger_cron": auto_trigger_cron,
    }


def get_skill_info(name: str) -> Optional[Dict[str, Any]]:
    """获取某个技能的触发信息。"""
    registry = _load_registry()
    return registry.get(name)


def get_skills_by_scenario(scenario_hint: str) -> List[Dict[str, Any]]:
    """通过场景关键词搜索匹配的技能。"""
    hint_lower = scenario_hint.lower()
    registry = _load_registry()
    results = []
    for info in registry.values():
        if hint_lower in info.get("trigger_scenarios", "").lower():
            results.append(info)
            continue
        for kw in info.get("trigger_keywords", []):
            if kw in hint_lower:
                results.append(info)
                break
    return results


def get_all_skills_requiring_api() -> List[str]:
    """获取所有需要外部 API 的技能列表。"""
    registry = _load_registry()
    return [n for n, i in registry.items() if i.get("requires_external_api")]


def get_available_skills_text() -> str:
    """生成用于系统提示词注入的可用技能文本。"""
    registry = _load_registry()
    lines = ["## 可用技能", "", "| 技能名称 | 触发词/场景 | 是否需要外部 API |", "|----------|-------------|-----------------|"]
    for name in sorted(registry.keys()):
        info = registry[name]
        triggers = ", ".join(info.get("trigger_keywords", [])[:3])
        if len(info.get("trigger_keywords", [])) > 3:
            triggers += "..."
        if not triggers:
            triggers = info.get("trigger_scenarios", "-")[:40]
        req_api = "✅" if info.get("requires_external_api") else "❌"
        lines.append(f"| {name} | {triggers} | {req_api} |")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════
# 自动检测与注册新技能
# ════════════════════════════════════════════════════════════════


def _parse_skill_md(md_path: Path) -> tuple:
    """解析 SKILL.md，提取元数据+正文。"""
    text = md_path.read_text(encoding="utf-8", errors="ignore")
    if text.startswith("---"):
        parts = text.split("---", 2)
        meta = parts[1] if len(parts) >= 3 else ""
        body = parts[2] if len(parts) >= 3 else text
    else:
        meta = ""
        body = text
    return text, meta, body


def _extract_trigger_keywords(body: str, meta: str, description: str) -> List[str]:
    """从 SKILL.md 中提取触发关键词，优先级：显式触发词 > Use When > 描述推断。"""
    keywords = []

    # 1. 中文触发词
    for m in re.finditer(r'(?:触发词|触发条件|激活条件|调用条件)[:：]\s*(.+?)(?:\n\n|\n###|\n---|$)', body, re.DOTALL):
        kws = [w.strip() for w in re.split(r'[,;，；、\n]+', m.group(1)) if len(w.strip()) > 1]
        keywords.extend(kws)

    # 2. Trigger phrases / Keywords that trigger
    for pattern in [r'[Tt]rigger\s+[Pp]hrases?[:：\s]+(.+?)(?:\n\n|\n###|\n---|$)',
                    r'[Kk]eywords?\s+that\s+trigger[:：\s]+(.+?)(?:\n\n|\n###|\n---|$)']:
        for m in re.finditer(pattern, body, re.DOTALL):
            kws = [w.strip().strip('"').strip("'") for w in re.split(r'[,;，；、\n]+', m.group(1)) if len(w.strip()) > 1]
            keywords.extend(kws)

    # 3. metadata keywords
    m = re.search(r'"keywords"\s*:\s*\[(.+?)\]', meta if meta else body, re.DOTALL)
    if m:
        kws = re.findall(r'"([^"]+)"', m.group(1))
        keywords.extend(kws)

    # 4. "Use when" description → extract key nouns
    if not keywords and "Use when" in description:
        use_when = description[description.find("Use when"):description.find("Use when") + 300].split(".")[0]
        kw_part = re.search(r'user\s+(?:mentions|asks|wants|needs|says)\s+(.+?)(?:\.|$)', use_when, re.IGNORECASE)
        if kw_part:
            kws = [w.strip() for w in re.split(r'[,;、]+', kw_part.group(1)) if len(w.strip()) > 2]
            keywords.extend(kws)

    # 5. Fallback: skill name as human-readable trigger
    if not keywords:
        human_name = md_path.parent.name.replace("-", " ").replace("_", " ")
        if human_name.count(" ") <= 3:
            keywords.append(human_name)

    # Deduplicate
    seen = set()
    deduped = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            deduped.append(kw)
    return deduped[:8]


def _extract_scenario(meta: str, body: str, description: str) -> str:
    """提取触发场景描述。"""
    # 优先使用 description 中的 Use when
    if "Use when" in description or "use when" in description:
        return description[:250]
    # 其次 body 中的 Use when 长描述
    m = re.search(r'(?:[Uu]se\s+(?:this\s+)?[Ww]hen|When to [Uu]se)[:：\s]+(.+?)(?:\n\n|\n###|\n---|$)', body, re.DOTALL)
    if m:
        return m.group(1).strip()[:250]
    # 最后 description 本身
    return description[:200]


def _extract_description(meta: str, body: str) -> str:
    """从 frontmatter 提取描述。"""
    # Try YAML description field
    dm = re.search(r'description:\s*"(.+?)"\s*$', meta if meta else "", re.DOTALL)
    if not dm:
        dm = re.search(r"description:\s*'(.+?)'\s*$", meta if meta else "", re.DOTALL)
    if not dm:
        dm = re.search(r'description:\s*\|\s*\n(.+?)(?:\n\S)', meta if meta else "", re.DOTALL)
    return dm.group(1)[:200] if dm else (body.split("\n")[0][:200] if body else "")


def _extract_external_api(body: str, meta: str) -> bool:
    """判断技能是否需要外部 API。"""
    if '"requires"' in meta or '"bins"' in meta or '"env"' in meta:
        return True
    for key in ["BAIDU_API_KEY", "OPENAI_API_KEY", "AMINER_API_KEY", "DEEPL_API_KEY", "ANTHROPIC_API_KEY"]:
        if key in body or key in meta:
            return True
    for svc in ["api.", "baidu.com", "openai.com", "arxiv.org", "aminer.cn", "wttr.in"]:
        if svc in body or svc in meta:
            return True
    if "curl" in body.lower() or "web_fetch" in body:
        return True
    return False


def _extract_env_vars(meta: str, body: str) -> list:
    """提取所需环境变量列表。"""
    env_vars = []
    m = re.search(r'"env"\s*:\s*\[([^\]]*)\]', meta if meta else body, re.DOTALL)
    if m:
        env_vars = re.findall(r'"([^"]+)"', m.group(1))
    pm = re.search(r'primaryEnv\s*:\s*"([^"]+)"', meta if meta else "")
    if pm and pm.group(1) not in env_vars:
        env_vars.append(pm.group(1))
    return env_vars


def _extract_bins(meta: str) -> list:
    """提取所需系统工具。"""
    m = re.search(r'"bins"\s*:\s*\[([^\]]*)\]', meta if meta else "", re.DOTALL)
    return re.findall(r'"([^"]+)"', m.group(1)) if m else []


def _extract_cron_trigger(body: str) -> str:
    """提取定时触发 cron 表达式。"""
    m = re.search(r'每天(\d{1,2}):(\d{2})\s*(?:定时|自动)', body)
    return f"{m.group(2)} {m.group(1)} * * *" if m else ""


def _infer_category(name: str, body_lower: str) -> str:
    """根据技能名称和内容推断分类。"""
    if "finance" in body_lower or "stock" in body_lower or "market" in body_lower:
        return "finance"
    if "weather" in body_lower:
        return "weather"
    if "news" in body_lower or "news" in name.lower():
        return "news"
    if any(w in body_lower for w in ["comic", "picture", "image", "music", "video"]):
        return "media"
    if any(w in body_lower for w in ["writing", "article", "创作", "写作", "文案"]):
        return "writing"
    if any(w in body_lower for w in ["code", "program", "python", "javascript", "api", "tool"]):
        return "development"
    if any(w in body_lower for w in ["health", "健身", "fitness", "diet", "exercise"]):
        return "health"
    if any(w in body_lower for w in ["education", "exam", "study", "学习", "考试", "课程"]):
        return "education"
    return "general"


# ════════════════════════════════════════════════════════════════
# 公开 API
# ════════════════════════════════════════════════════════════════


def register_skill(skill_name: str, *, force: bool = False) -> dict:
    """注册单个技能到注册表。返回操作结果。"""
    skill_path = SKILLS_DIR / skill_name
    md_path = skill_path / "SKILL.md"

    if not md_path.exists():
        return {"status": "error", "message": f"skills/{skill_name}/SKILL.md 不存在"}

    # Load existing registry
    registry = _load_registry()
    if skill_name in registry and not force:
        return {"status": "skipped", "message": f"{skill_name} 已注册（使用 force=True 覆盖）"}

    # Parse
    text, meta, body = _parse_skill_md(md_path)
    description = _extract_description(meta, body)
    body_lower = body.lower()[:500]

    trigger_kws = _extract_trigger_keywords(body, meta, description)
    scenario = _extract_scenario(meta, body, description)
    needs_api = _extract_external_api(body, meta)
    env_vars = _extract_env_vars(meta, body)
    bins = _extract_bins(meta)
    cron = _extract_cron_trigger(body)
    category = _infer_category(skill_name, body_lower)

    # Merge with existing data if present
    if skill_name in registry:
        existing = registry[skill_name]
        # Preserve manual data, only override if empty or when auto-detected
        final = {
            "name": skill_name,
            "trigger_keywords": trigger_kws or existing.get("trigger_keywords", []),
            "trigger_scenarios": scenario or existing.get("trigger_scenarios", ""),
            "requires_external_api": needs_api or existing.get("requires_external_api", False),
            "requires_env_vars": env_vars or existing.get("requires_env_vars", []),
            "requires_bins": bins or existing.get("requires_bins", []),
            "category": category if category != "general" else existing.get("category", "general"),
            "description": description or existing.get("description", ""),
            "is_system_skill": existing.get("is_system_skill", False),
            "auto_trigger_cron": cron or existing.get("auto_trigger_cron", ""),
        }
    else:
        final = {
            "name": skill_name,
            "trigger_keywords": trigger_kws,
            "trigger_scenarios": scenario,
            "requires_external_api": needs_api,
            "requires_env_vars": env_vars,
            "requires_bins": bins,
            "category": category,
            "description": description,
            "is_system_skill": False,
            "auto_trigger_cron": cron,
        }

    registry[skill_name] = final
    _save_registry()

    return {
        "status": "registered" if skill_name not in [_TRIGGER_REGISTRY.get(skill_name)] else "updated",
        "message": f"{skill_name} 已注册（分类: {category}, 触发词: {len(trigger_kws)}个, 需要API: {needs_api}）",
        "data": final,
    }


def scan_new_skills() -> List[str]:
    """扫描 skills/ 目录，找出未注册的技能。"""
    registry = _load_registry()
    new_skills = []
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        name = skill_dir.name
        if name in registry:
            continue
        if (skill_dir / "SKILL.md").exists():
            new_skills.append(name)
    return new_skills


def auto_register_new_skills(*, verbose: bool = True) -> int:
    """自动检测并注册所有新技能。返回注册数量。"""
    registry = _load_registry()
    new_skills = scan_new_skills()
    count = 0

    for name in new_skills:
        result = register_skill(name, force=False)
        if result["status"] in ("registered", "updated"):
            if verbose:
                api_tag = "🌐" if result['data'].get('requires_external_api') else "🖥️"
                kws = len(result['data'].get('trigger_keywords', []))
                print(f"  {api_tag} {name} — 分类: {result['data']['category']}, 触发词: {kws}个")
            count += 1

    if verbose:
        total = len(_load_registry())
        print(f"\n📊 新技能: {count} 个, 注册表总数: {total}")

    return count


# ════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2:
        cmd = sys.argv[1]
        if cmd == "info":
            name = sys.argv[2] if len(sys.argv) > 2 else ""
            if name:
                info = get_skill_info(name)
                print(json.dumps(info, ensure_ascii=False, indent=2) if info else f"技能 '{name}' 未注册")
            else:
                registry = _load_registry()
                print(json.dumps(registry, ensure_ascii=False, indent=2))
        elif cmd == "scan":
            new = scan_new_skills()
            if new:
                print(f"发现 {len(new)} 个新技能:")
                for n in new:
                    print(f"  - {n}")
            else:
                print("无新技能")
        elif cmd == "register":
            name = sys.argv[2] if len(sys.argv) > 2 else ""
            if name:
                result = register_skill(name)
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
            else:
                print("请指定技能名称")
        elif cmd == "auto":
            count = auto_register_new_skills()
            print(f"注册了 {count} 个新技能")
        elif cmd == "list":
            registry = _load_registry()
            print(f"共 {len(registry)} 个技能")
            for name in sorted(registry.keys()):
                info = registry[name]
                api = "🌐" if info.get("requires_external_api") else "🖥️"
                kws = ", ".join(info.get("trigger_keywords", [])[:3])
                print(f"  {api} {name} — {kws}")
        else:
            print(f"用法: python3 -m core.skill_rules_engine <info|scan|register|auto|list>")
    else:
        # Default: auto-register + display summary
        count = auto_register_new_skills()
        registry = _load_registry()
        print(f"技能规则化引擎就绪 — {len(registry)} 个技能已注册")
