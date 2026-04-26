#!/usr/bin/env python3
"""同步 skill_registry.json 与 skills/ 目录"""

import json
from pathlib import Path
from datetime import datetime

SCAN_RESULT_FILE = Path("infrastructure/inventory/skill_scan_result.json")
SKILL_REGISTRY_FILE = Path("infrastructure/inventory/skill_registry.json")
FUSION_INDEX_FILE = Path("infrastructure/inventory/fusion_index.json")


def sync_skill_registry():
    """同步技能注册表"""
    # 读取扫描结果
    if not SCAN_RESULT_FILE.exists():
        print("❌ 请先运行 scan_skills.py")
        return
    
    scan_result = json.loads(SCAN_RESULT_FILE.read_text())
    
    # 读取现有注册表
    if SKILL_REGISTRY_FILE.exists():
        registry = json.loads(SKILL_REGISTRY_FILE.read_text())
    else:
        registry = {"version": "1.0.0", "skills": {}, "stats": {}}
    
    # 同步技能
    registry["version"] = "9.1.0"
    registry["updated"] = datetime.now().strftime("%Y-%m-%d")
    registry["skills"] = {}
    
    for skill_name, skill_info in scan_result["skills"].items():
        registry["skills"][skill_name] = {
            "name": skill_name,
            "path": skill_info["path"],
            "status": skill_info["status"],
            "has_skill_md": skill_info["has_skill_md"],
            "is_executable": skill_info["is_executable"],
            "is_document_only": skill_info["is_document_only"],
            "python_files": skill_info["python_files"],
        }
    
    # 更新统计
    registry["stats"] = {
        "total": len(registry["skills"]),
        "active": sum(1 for s in registry["skills"].values() if s["status"] == "active"),
        "document_only": sum(1 for s in registry["skills"].values() if s["status"] == "document_only"),
        "invalid": sum(1 for s in registry["skills"].values() if s["status"] == "invalid"),
    }
    
    # 保存
    SKILL_REGISTRY_FILE.write_text(json.dumps(registry, indent=2, ensure_ascii=False))
    print(f"✅ skill_registry.json 已同步")
    print(f"   total: {registry['stats']['total']}")
    print(f"   active: {registry['stats']['active']}")
    print(f"   document_only: {registry['stats']['document_only']}")
    print(f"   invalid: {registry['stats']['invalid']}")
    
    return registry


def sync_fusion_index(registry):
    """同步 fusion_index.json"""
    if not FUSION_INDEX_FILE.exists():
        fusion = {"version": "9.1.0", "updated": datetime.now().strftime("%Y-%m-%d")}
    else:
        fusion = json.loads(FUSION_INDEX_FILE.read_text())
    
    fusion["version"] = "9.1.0"
    fusion["updated"] = datetime.now().strftime("%Y-%m-%d")
    fusion["skills"] = {
        "total": registry["stats"]["total"],
        "local_skill_dirs": registry["stats"]["total"],
        "registered_skills": registry["stats"]["total"],
        "active_skills": registry["stats"]["active"],
        "document_only_skills": registry["stats"]["document_only"],
        "invalid_skills": registry["stats"]["invalid"],
    }
    
    FUSION_INDEX_FILE.write_text(json.dumps(fusion, indent=2, ensure_ascii=False))
    print(f"\n✅ fusion_index.json 已同步")
    print(f"   skills.total: {fusion['skills']['total']}")


def main():
    print("🔄 同步 skill_registry.json...")
    registry = sync_skill_registry()
    
    print("\n🔄 同步 fusion_index.json...")
    sync_fusion_index(registry)


if __name__ == "__main__":
    main()
