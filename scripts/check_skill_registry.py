#!/usr/bin/env python3
"""检查 skill_registry.json 状态"""

import json
from pathlib import Path

SKILL_REGISTRY_FILE = Path("infrastructure/inventory/skill_registry.json")
FUSION_INDEX_FILE = Path("infrastructure/fusion_index.json")


def check_skill_registry():
    """检查技能注册表"""
    print("=" * 60)
    print("  Skill Registry 检查")
    print("=" * 60)
    
    if not SKILL_REGISTRY_FILE.exists():
        print("❌ skill_registry.json 不存在")
        return
    
    registry = json.loads(SKILL_REGISTRY_FILE.read_text())
    
    print(f"\n📋 注册表版本: {registry.get('version', 'N/A')}")
    print(f"📅 更新时间: {registry.get('updated', 'N/A')}")
    
    stats = registry.get("stats", {})
    print(f"\n📊 统计:")
    print(f"   total: {stats.get('total', 0)}")
    print(f"   active: {stats.get('active', 0)}")
    print(f"   document_only: {stats.get('document_only', 0)}")
    print(f"   invalid: {stats.get('invalid', 0)}")
    
    # 检查 skills/ 实际目录
    skills_dir = Path("skills")
    if skills_dir.exists():
        actual_count = len([d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith(".")])
        registered_count = len(registry.get("skills", {}))
        
        print(f"\n🔍 一致性检查:")
        print(f"   skills/ 实际目录: {actual_count}")
        print(f"   skill_registry 登记: {registered_count}")
        
        if actual_count == registered_count:
            print(f"   ✅ 数量一致")
        else:
            print(f"   ⚠️  数量不一致，差异: {abs(actual_count - registered_count)}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    check_skill_registry()
