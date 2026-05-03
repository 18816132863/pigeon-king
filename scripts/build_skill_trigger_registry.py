#!/usr/bin/env python3
"""
Build skill trigger registry — scan all skills/ SKILL.md files
and extract trigger keywords, scenarios, API requirements, etc.
"""
from __future__ import annotations
import json, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Load the registry module
sys.path.insert(0, str(ROOT))
from core.skill_trigger_registry import register, save_registry

SKILLS_DIR = ROOT / "skills"

# Patterns to extract from each SKILL.md
TRIGGER_PATTERNS = [
    # "触发词：..." style
    (r'触发词[:：]\s*(.+)', 'trigger_keywords'),
    # "Triggers: ..." style
    (r'Triggers?[:：\s]+(.+)', 'trigger_keywords'),
    # "keywords that trigger" style
    (r'Keywords? that trigger[:：\s]+(.+)', 'trigger_keywords'),
    # "Use when" / "use this skill when"
    (r'[Uu]se\s+(?:this\s+)?[Ww]hen[:：\s]+(.+)', 'scenario'),
    # "Trigger this skill when"
    (r'[Tt]rigger\s+(?:this\s+)?[Ss]kill\s+[Ww]hen[:：\s]+(.+)', 'scenario'),
    # "description:" field
    (r'description:\s*"(.+?)"', 'description'),
    (r"description:\s*'(.+?)'", 'description'),
    # "cron" / "定时触发"
    (r'[\d:]{4,8}\s+定时触发', 'cron'),
    (r'\d+\s+(?:分钟|小时|天)\s+(?:后|之后)?\s*触发', 'cron'),
]

ENV_PATTERNS = [
    (r'env["\']?\s*:\s*\[([^\]]+)\]', 'env_vars'),
    (r'primaryEnv["\']?\s*:\s*"([^"]+)"', 'primary_env'),
    (r'"requires":\s*\{', 'requires_block'),
]

BIN_PATTERNS = [
    (r'"bins["\']?\s*:\s*\[([^\]]+)\]', 'bins'),
]

# Known API keys and what they mean
API_KEYS = {
    'BAIDU_API_KEY': 'baidu_ai',
    'AMINER_API_KEY': 'aminer',
    'OPENAI_API_KEY': 'openai',
    'YOUR_API_KEY': 'generic',
    'ANTHROPIC_API_KEY': 'anthropic',
    'DEEPL_API_KEY': 'deepl',
}


def parse_trigger_keywords(text: str) -> list:
    """Parse comma/separator delimited keywords from text."""
    # Remove quotes
    text = text.strip().strip('"').strip("'")
    # Split by common delimiters
    parts = re.split(r'[,;、，；\n]+', text)
    keywords = []
    for p in parts:
        p = p.strip().strip('"').strip("'").strip()
        if not p:
            continue
        # Remove prefixes like "触发词："
        p = re.sub(r'^(?:触发词|Triggers?|Keywords?).*?[:：]\s*', '', p)
        if p and len(p) > 1 and p not in keywords:
            keywords.append(p)
    return keywords[:10]  # limit to 10


def parse_scenario(text: str) -> str:
    """Clean up scenario text."""
    text = text.strip().strip('"').strip("'")
    # Remove "Use when:" prefix
    text = re.sub(r'^(?:[Uu]se\s+(?:this\s+)?[Ww]hen|Trigger\s+(?:this\s+)?[Ss]kill\s+[Ww]hen)\s*[:：]?\s*', '', text)
    return text[:300]


def parse_env_vars(text: str) -> list:
    """Extract env var names from JSON-like array text."""
    vars_found = []
    # Extract quoted strings
    for m in re.finditer(r'"([A-Z_]+)"', text):
        vars_found.append(m.group(1))
    # Also check for primaryEnv
    for m in re.finditer(r'primaryEnv["\']?\s*:\s*"([^"]+)"', text):
        if m.group(1) not in vars_found:
            vars_found.append(m.group(1))
    return vars_found


def has_external_api(skill_text: str, metadata_text: str) -> bool:
    """Determine if skill requires external API."""
    # Check metadata requires block
    if '"requires"' in metadata_text or '"bins"' in metadata_text or '"env"' in metadata_text:
        return True
    # Check for API key references
    for key in API_KEYS:
        if key in skill_text:
            return True
    # Check for specific external services
    services = [
        'baidu.com', 'openai.com', 'v2ex.com', 'arxiv.org',
        'aminer.cn', 'wttr.in', 'api.', 'https://', 'http://',
    ]
    for svc in services:
        if svc in skill_text:
            return True
    # Check for curl requirement
    if 'curl' in skill_text.lower() or 'web_fetch' in skill_text:
        return True
    return False


def process_all_skills():
    """Scan all skills and register them."""
    count = 0
    errors = []
    
    for skill_dir in sorted(SKILLS_DIR.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_path = skill_dir / "SKILL.md"
        if not skill_path.exists():
            continue
        
        skill_name = skill_dir.name
        skill_text = skill_path.read_text(encoding="utf-8", errors="ignore")
        metadata_text = ""
        
        # Extract metadata block (YAML frontmatter)
        if skill_text.startswith('---'):
            parts = skill_text.split('---', 2)
            if len(parts) >= 3:
                metadata_text = parts[1]
                body_text = parts[2]
            else:
                body_text = skill_text
        else:
            body_text = skill_text
        
        # Parse triggers from metadata
        trigger_keywords = []
        trigger_scenario = ""
        description = ""
        auto_cron = ""
        env_vars = []
        bins = []
        
        # Parse from metadata description field
        desc_match = re.search(r'description:\s*"(.+?)"', metadata_text)
        if not desc_match:
            desc_match = re.search(r"description:\s*'(.+?)'", metadata_text)
        if desc_match:
            description = desc_match.group(1)
            # Check if description contains trigger info
            if "Use when" in description or "use when" in description:
                trigger_scenario = description
            for kw in ["触发词", "Triggers", "Keywords"]:
                if kw in description:
                    kw_part = re.split(r'\.\s+', description)[:1]
                    parsed = parse_trigger_keywords(description)
                    if parsed:
                        trigger_keywords.extend(parsed)
        
        # Parse from body text
        body_lower = body_text.lower()
        
        # Trigger keywords from body
        # 触发词 pattern
        for m in re.finditer(r'(?:触发词|触发条件|激活条件|调用条件)[:：]\s*(.+?)(?:\n\n|\n###|\n---|$)', body_text, re.DOTALL):
            kws = parse_trigger_keywords(m.group(1))
            trigger_keywords.extend(kws)
        
        # Trigger phrases from body
        for m in re.finditer(r'[Tt]rigger\s+phrases?[:：\s]+(.+?)(?:\n\n|\n###|\n---|$)', body_text, re.DOTALL):
            kws = parse_trigger_keywords(m.group(1))
            trigger_keywords.extend(kws)
        
        # "Keywords that trigger" pattern
        for m in re.finditer(r'[Kk]eywords?\s+that\s+trigger[:：\s]+(.+?)(?:\n\n|\n###|\n---|$)', body_text, re.DOTALL):
            kws = parse_trigger_keywords(m.group(1))
            trigger_keywords.extend(kws)
        
        # "Use when" from body (longer form)
        use_when_match = re.search(r'(?:Use when|When to [Uu]se|[Uu]se this [Ss]kill when)[:：\s]+(.+?)(?:\n\n|\n###|\n---|(?=\n\d+\.)|$)', body_text, re.DOTALL)
        if use_when_match:
            scenario = parse_scenario(use_when_match.group(1))
            if scenario and not trigger_scenario:
                trigger_scenario = scenario[:250]
        
        # "Trigger this skill when" from body
        trig_when_match = re.search(r'[Tt]rigger\s+(?:this\s+)?[Ss]kill\s+[Ww]hen[:：\s]+(.+?)(?:\n\n|\n###|\n---|$)', body_text, re.DOTALL)
        if trig_when_match:
            scenario = parse_scenario(trig_when_match.group(1))
            if scenario and not trigger_scenario:
                trigger_scenario = scenario[:250]
        
        # Cron/定时 from body
        cron_match = re.search(r'每天(\d{1,2}):(\d{2})\s*(?:定时|自动)', body_text)
        if cron_match:
            auto_cron = f"{cron_match.group(2)} {cron_match.group(1)} * * *"
        
        # API/Env requirements from metadata
        if '"bins"' in metadata_text:
            bin_match = re.search(r'"bins"\s*:\s*\[([^\]]*)\]', metadata_text)
            if bin_match:
                bins_text = bin_match.group(1)
                bins = re.findall(r'"([^"]+)"', bins_text)
        
        if '"env"' in metadata_text:
            env_match = re.search(r'"env"\s*:\s*\[([^\]]*)\]', metadata_text)
            if env_match:
                env_text = env_match.group(1)
                env_vars = re.findall(r'"([^"]+)"', env_text)
        
        primary_env_match = re.search(r'primaryEnv\s*:\s*"([^"]+)"', metadata_text)
        if primary_env_match:
            if primary_env_match.group(1) not in env_vars:
                env_vars.append(primary_env_match.group(1))
        
        # Determine category from metadata
        cat_match = re.search(r'category\s*:\s*"([^"]+)"', metadata_text)
        category = cat_match.group(1) if cat_match else "general"
        if not category or category == "skill":
            # Try to infer
            if "finance" in body_lower or "stock" in body_lower or "market" in body_lower:
                category = "finance"
            elif "weather" in body_lower:
                category = "weather"
            elif "news" in body_lower or "news" in skill_name.lower():
                category = "news"
            elif "comic" in body_lower or "picture" in body_lower or "image" in body_lower:
                category = "media"
            elif "writing" in body_lower or "article" in body_lower or "创作" in body_lower or "写作" in body_lower:
                category = "writing"
            elif "code" in body_lower or "program" in body_lower or "python" in body_lower:
                category = "development"
            elif "health" in body_lower or "健身" in body_lower or "fitness" in body_lower:
                category = "health"
            elif "education" in body_lower or "exam" in body_lower or "study" in body_lower or "学习" in body_lower:
                category = "education"
            else:
                category = "general"
        
        # Deduplicate keywords
        seen = set()
        trigger_keywords_deduped = []
        for kw in trigger_keywords:
            if kw not in seen:
                seen.add(kw)
                trigger_keywords_deduped.append(kw)
        
        requires_api = has_external_api(body_text, metadata_text)
        is_system = skill_name in [
            "Assistant", "agent-builder", "soulcraft", "today-task",
            "skill-creator", "proactive-agent", "smart-followups",
        ]
        
        # If no trigger keywords found, try to extract from description
        if not trigger_keywords_deduped:
            # Try getting from skill name
            if skill_name in ["weather", "fitness-coach", "fasting-tracker"]:
                pass  # These have Use When descriptions
            # Use first 3 meaningful words of description as fallback
            if description:
                # Extract distinct words as potential triggers
                words = re.findall(r'[\u4e00-\u9fff\w]{2,}', description[:100])
                trigger_keywords_deduped = words[:5]
        
        # Register
        try:
            register(
                skill_name,
                trigger_keywords=trigger_keywords_deduped,
                trigger_scenarios=trigger_scenario,
                requires_external_api=requires_api,
                requires_env_vars=env_vars,
                requires_bins=bins,
                category=category,
                description=description[:200] if description else "",
                is_system_skill=is_system,
                auto_trigger_cron=auto_cron,
            )
            count += 1
        except Exception as e:
            errors.append(f"{skill_name}: {e}")
    
    return count, errors


if __name__ == "__main__":
    count, errors = process_all_skills()
    reg_path = save_registry()
    
    print(f"✅ 注册了 {count} 个技能")
    print(f"📁 注册表已保存: {reg_path}")
    print(f"📏 大小: {reg_path.stat().st_size // 1024}KB")
    
    if errors:
        print(f"\n⚠️  以下技能注册时出错:")
        for e in errors:
            print(f"   ❌ {e}")
    
    # Print summary by category
    import collections
    from core.skill_trigger_registry import TRIGGER_REGISTRY
    
    cats = collections.Counter()
    api_skills = []
    for name, info in TRIGGER_REGISTRY.items():
        cats[info["category"]] += 1
        if info["requires_external_api"]:
            api_skills.append(name)
    
    print(f"\n📊 按分类统计:")
    for cat, cnt in cats.most_common():
        print(f"   {cat}: {cnt}")
    
    print(f"\n🌐 需要外部 API 的技能: {len(api_skills)}")
    print(f"   (离线模式下不可用)")
    
    # Display sample
    print(f"\n📋 示例 - skill_trigger_registry.py get_available_skills_text():")
    from core.skill_trigger_registry import get_available_skills_text
    print(get_available_skills_text()[:800])
