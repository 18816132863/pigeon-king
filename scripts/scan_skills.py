#!/usr/bin/env python3
"""扫描 skills/ 目录，生成真实技能清单"""

import json
from pathlib import Path
from datetime import datetime

SKILLS_DIR = Path("skills")
OUTPUT_FILE = Path("infrastructure/inventory/skill_scan_result.json")


def scan_skills():
    """扫描 skills 目录"""
    result = {
        "scan_time": datetime.now().isoformat(),
        "skills": {},
        "stats": {
            "skill_dir_count": 0,
            "skill_file_count": 0,
            "valid_skill_count": 0,
            "invalid_skill_count": 0,
            "executable_skill_count": 0,
            "document_only_skill_count": 0,
        }
    }
    
    if not SKILLS_DIR.exists():
        print("❌ skills/ 目录不存在")
        return result
    
    # 扫描每个技能目录
    for skill_dir in SKILLS_DIR.iterdir():
        if not skill_dir.is_dir():
            continue
        if skill_dir.name.startswith(".") or skill_dir.name.startswith("_"):
            continue
            
        result["stats"]["skill_dir_count"] += 1
        
        skill_name = skill_dir.name
        skill_info = {
            "name": skill_name,
            "path": str(skill_dir),
            "has_skill_md": False,
            "has_init_py": False,
            "has_main_py": False,
            "has_scripts": False,
            "python_files": 0,
            "is_valid": False,
            "is_executable": False,
            "is_document_only": False,
            "status": "unknown"
        }
        
        # 检查 SKILL.md
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            skill_info["has_skill_md"] = True
            skill_info["is_valid"] = True
        
        # 检查 Python 文件
        py_files = list(skill_dir.glob("**/*.py"))
        skill_info["python_files"] = len(py_files)
        result["stats"]["skill_file_count"] += len(py_files)
        
        # 检查 __init__.py
        if (skill_dir / "__init__.py").exists():
            skill_info["has_init_py"] = True
            skill_info["is_executable"] = True
        
        # 检查 main.py 或 scripts/
        if (skill_dir / "main.py").exists():
            skill_info["has_main_py"] = True
            skill_info["is_executable"] = True
        
        if (skill_dir / "scripts").exists() and list((skill_dir / "scripts").glob("*.py")):
            skill_info["has_scripts"] = True
            skill_info["is_executable"] = True
        
        # 判断状态
        if skill_info["is_valid"]:
            result["stats"]["valid_skill_count"] += 1
            if skill_info["is_executable"]:
                result["stats"]["executable_skill_count"] += 1
                skill_info["status"] = "active"
            else:
                result["stats"]["document_only_skill_count"] += 1
                skill_info["is_document_only"] = True
                skill_info["status"] = "document_only"
        else:
            result["stats"]["invalid_skill_count"] += 1
            skill_info["status"] = "invalid"
        
        result["skills"][skill_name] = skill_info
    
    return result


def main():
    print("🔍 扫描 skills/ 目录...")
    result = scan_skills()
    
    # 保存结果
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    
    print(f"\n✅ 扫描完成，结果保存到 {OUTPUT_FILE}")
    print(f"\n📊 统计:")
    print(f"   skill_dir_count: {result['stats']['skill_dir_count']}")
    print(f"   skill_file_count: {result['stats']['skill_file_count']}")
    print(f"   valid_skill_count: {result['stats']['valid_skill_count']}")
    print(f"   executable_skill_count: {result['stats']['executable_skill_count']}")
    print(f"   document_only_skill_count: {result['stats']['document_only_skill_count']}")
    print(f"   invalid_skill_count: {result['stats']['invalid_skill_count']}")


if __name__ == "__main__":
    main()
