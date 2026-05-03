#!/usr/bin/env python3
"""
技能触发注册表 — 统一登记所有技能的触发方式和条件

每个技能记录以下字段：
- name: 技能名称
- trigger_keywords: 触发关键词列表（用户说这些词时触发的概率最高）
- trigger_scenarios: 触发场景描述（自然语言描述什么情况适合触发）
- requires_external_api: 是否需要外部 API（离线模式下不可用）
- requires_env_vars: 需要哪些环境变量（API key 等）
- requires_bins: 需要哪些系统二进制工具
- category: 技能分类
- description: 技能描述
- is_system_skill: 是否为系统内置技能（不可卸载）
- auto_trigger_cron: 如果有定时触发规则的 cron 表达式

用于生成 available_skills 提示词注入和技能发现。
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
REGISTRY_FILE = ROOT / "governance" / "skill_trigger_registry.json"


# ════════════════════════════════════════════════════════════════
# 技能触发定义结构
# ════════════════════════════════════════════════════════════════

TRIGGER_REGISTRY: Dict[str, Dict[str, Any]] = {}


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
    TRIGGER_REGISTRY[name] = {
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


def get_skill_trigger_info(name: str) -> Optional[Dict[str, Any]]:
    """获取某个技能的触发信息。"""
    return TRIGGER_REGISTRY.get(name)


def get_skills_by_scenario(scenario: str) -> List[Dict[str, Any]]:
    """通过场景关键词搜索匹配的技能。"""
    scenario_lower = scenario.lower()
    results = []
    for name, info in TRIGGER_REGISTRY.items():
        if scenario_lower in info["trigger_scenarios"].lower():
            results.append(info)
            continue
        for kw in info["trigger_keywords"]:
            if kw in scenario_lower:
                results.append(info)
                break
    return results


def get_skills_requiring_api() -> List[str]:
    """获取所有需要外部 API 的技能列表。"""
    return [n for n, i in TRIGGER_REGISTRY.items() if i["requires_external_api"]]


def get_available_skills_text() -> str:
    """生成用于系统提示词注入的可用技能文本。"""
    lines = []
    lines.append("## 可用技能")
    lines.append("")
    lines.append("| 技能名称 | 触发词/场景 | 是否需要外部 API |")
    lines.append("|----------|-------------|-----------------|")
    for name in sorted(TRIGGER_REGISTRY.keys()):
        info = TRIGGER_REGISTRY[name]
        if info["trigger_keywords"]:
            triggers = ", ".join(info["trigger_keywords"][:3])
            if len(info["trigger_keywords"]) > 3:
                triggers += "..."
        else:
            triggers = info["trigger_scenarios"][:40] if info["trigger_scenarios"] else "-"
        req_api = "✅" if info["requires_external_api"] else "❌"
        lines.append(f"| {name} | {triggers} | {req_api} |")
    return "\n".join(lines)


def save_registry() -> Path:
    """将注册表保存到 JSON 文件。"""
    REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_FILE.write_text(
        json.dumps(TRIGGER_REGISTRY, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    return REGISTRY_FILE


def load_registry() -> Dict[str, Any]:
    """从 JSON 文件加载注册表。"""
    if REGISTRY_FILE.exists():
        return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))
    return {}


if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "info":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        if name:
            info = get_skill_trigger_info(name)
            if info:
                print(json.dumps(info, ensure_ascii=False, indent=2))
            else:
                print(f"技能 '{name}' 未注册")
        else:
            print(json.dumps(TRIGGER_REGISTRY, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"status": "ok", "count": len(TRIGGER_REGISTRY)}, ensure_ascii=False, indent=2))
