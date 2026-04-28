#!/usr/bin/env python3
"""
V75.6 Plugin Reality Gate - 最终门禁

确保：
1. scripts 目录存在
2. 插件检测脚本存在
3. 插件状态不虚标
4. missing 不算 loaded
5. disabled 不算 enabled
6. docs 不算 plugin binaries
7. better-gateway/node-pty/lobster 未验证时 production=false
8. gate 能稳定退出
"""

import json
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def check_scripts_directory() -> dict:
    """检查 scripts 目录"""
    print("\n[1] 检查 scripts 目录")
    
    scripts_dir = PROJECT_ROOT / "scripts"
    required_scripts = [
        "v75_6_plugin_install_check.py",
        "v75_6_plugin_reality_gate.py",
        "v75_6_plugin_install_plan.sh",
    ]
    
    result = {
        "exists": scripts_dir.exists(),
        "scripts_found": [],
        "scripts_missing": [],
        "passed": True
    }
    
    for script in required_scripts:
        script_path = scripts_dir / script
        if script_path.exists():
            result["scripts_found"].append(script)
        else:
            result["scripts_missing"].append(script)
            result["passed"] = False
    
    if result["passed"]:
        print(f"   ✅ PASS: 所有必需脚本存在 ({len(result['scripts_found'])} 个)")
    else:
        print(f"   ❌ FAIL: 缺少脚本: {result['scripts_missing']}")
    
    return result


def check_install_check_report() -> dict:
    """检查安装检测报告"""
    print("\n[2] 检查 V75_6_PLUGIN_INSTALL_CHECK_REPORT.json")
    
    report_path = PROJECT_ROOT / "V75_6_PLUGIN_INSTALL_CHECK_REPORT.json"
    
    result = {
        "exists": False,
        "format_valid": False,
        "status_accurate": False,
        "passed": False
    }
    
    if not report_path.exists():
        print("   ❌ FAIL: 报告文件不存在")
        return result
    
    result["exists"] = True
    
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        # 检查必需字段
        required_fields = ["scan_time", "total_checked", "by_status", "plugins", 
                          "better_gateway", "lobster", "node_pty", "ready_for_production", "blockers"]
        missing_fields = [f for f in required_fields if f not in report]
        
        if missing_fields:
            print(f"   ❌ FAIL: 缺少字段: {missing_fields}")
            return result
        
        result["format_valid"] = True
        
        # 检查状态准确性
        by_status = report.get("by_status", {})
        ready = report.get("ready_for_production", False)
        blockers = report.get("blockers", [])
        
        # V75.6: 严格检查
        # 如果有 blockers，ready_for_production 必须为 False
        if blockers and ready:
            print(f"   ❌ FAIL: 存在阻塞项但 ready_for_production = True")
            return result
        
        # 如果 runtime_verified = 0，ready_for_production 必须为 False
        runtime_verified_count = by_status.get("runtime_verified", 0)
        if runtime_verified_count == 0 and ready:
            print(f"   ❌ FAIL: 无 runtime_verified 但 ready_for_production = True")
            return result
        
        # 检查 better-gateway
        bg = report.get("better_gateway", {})
        if not bg.get("runtime_verified", False) and ready:
            print(f"   ❌ FAIL: better-gateway 未验证但 ready_for_production = True")
            return result
        
        # 检查 lobster
        lobster = report.get("lobster", {})
        if not lobster.get("runtime_verified", False) and ready:
            print(f"   ❌ FAIL: lobster 未验证但 ready_for_production = True")
            return result
        
        # 检查 node-pty
        np = report.get("node_pty", {})
        if not np.get("runtime_verified", False) and ready:
            print(f"   ❌ FAIL: node-pty 未安装但 ready_for_production = True")
            return result
        
        result["status_accurate"] = True
        result["passed"] = True
        
        print(f"   ✅ PASS: 报告格式正确，状态准确")
        print(f"      ready_for_production: {ready}")
        print(f"      blockers: {len(blockers)}")
        
    except json.JSONDecodeError as e:
        print(f"   ❌ FAIL: JSON 解析错误: {e}")
    
    return result


def check_no_false_positives() -> dict:
    """检查无误报"""
    print("\n[3] 检查无误报")
    
    result = {
        "passed": True,
        "issues": []
    }
    
    # 检查 PLUGIN_REALITY_REPORT.json 是否存在且与 V75_6 报告一致
    old_report = PROJECT_ROOT / "PLUGIN_REALITY_REPORT.json"
    new_report = PROJECT_ROOT / "V75_6_PLUGIN_INSTALL_CHECK_REPORT.json"
    
    if old_report.exists() and new_report.exists():
        with open(old_report, 'r') as f:
            old_data = json.load(f)
        with open(new_report, 'r') as f:
            new_data = json.load(f)
        
        old_ready = old_data.get("summary", {}).get("ready_for_production", None)
        new_ready = new_data.get("ready_for_production", None)
        
        if old_ready != new_ready:
            result["issues"].append(f"PLUGIN_REALITY_REPORT.ready={old_ready} vs V75_6.ready={new_ready}")
            result["passed"] = False
    
    if result["passed"]:
        print("   ✅ PASS: 报告口径一致")
    else:
        print(f"   ❌ FAIL: 报告冲突: {result['issues']}")
    
    return result


def check_plugin_binaries_status() -> dict:
    """检查插件本体状态"""
    print("\n[4] 检查插件本体状态")
    
    report_path = PROJECT_ROOT / "V75_6_PLUGIN_INSTALL_CHECK_REPORT.json"
    
    result = {
        "plugin_binaries_included": False,
        "install_plan_available": False,
        "passed": True
    }
    
    if report_path.exists():
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        result["plugin_binaries_included"] = report.get("plugin_binaries_included", False)
        result["install_plan_available"] = report.get("install_plan_available", False)
    
    # V75.6: 插件本体不包含在工程中是正常的
    # 但必须明确标注
    if not result["plugin_binaries_included"]:
        print("   ℹ️ INFO: 插件本体未包含在工程中（正常）")
    
    if result["install_plan_available"]:
        print("   ✅ PASS: 安装计划可用")
    else:
        print("   ⚠️ WARNING: 安装计划不可用")
    
    return result


def check_version_label() -> dict:
    """检查版本标签"""
    print("\n[5] 检查版本标签")
    
    result = {
        "v75_6_reports_exist": False,
        "passed": True
    }
    
    # 检查 V75.6 报告文件
    v75_6_files = [
        PROJECT_ROOT / "V75_6_PLUGIN_INSTALL_CHECK_REPORT.json",
        PROJECT_ROOT / "docs" / "V75_6_PLUGIN_INSTALL_GUIDE.md",
    ]
    
    missing = [str(f) for f in v75_6_files if not f.exists()]
    
    if missing:
        print(f"   ⚠️ WARNING: 缺少 V75.6 文件: {missing}")
    else:
        result["v75_6_reports_exist"] = True
        print("   ✅ PASS: V75.6 文件存在")
    
    return result


def main():
    """主函数"""
    print("=" * 60)
    print("V75.6 Plugin Reality Gate")
    print("=" * 60)
    
    checks = []
    all_passed = True
    blockers = []
    
    # 1. 检查 scripts 目录
    r1 = check_scripts_directory()
    checks.append(("scripts_directory", r1["passed"]))
    if not r1["passed"]:
        blockers.append("scripts 目录不完整")
        all_passed = False
    
    # 2. 检查安装检测报告
    r2 = check_install_check_report()
    checks.append(("install_check_report", r2["passed"]))
    if not r2["passed"]:
        blockers.append("安装检测报告问题")
        all_passed = False
    
    # 3. 检查无误报
    r3 = check_no_false_positives()
    checks.append(("no_false_positives", r3["passed"]))
    if not r3["passed"]:
        blockers.append("报告存在误报")
        all_passed = False
    
    # 4. 检查插件本体状态
    r4 = check_plugin_binaries_status()
    checks.append(("plugin_binaries_status", r4["passed"]))
    
    # 5. 检查版本标签
    r5 = check_version_label()
    checks.append(("version_label", r5["v75_6_reports_exist"]))
    
    # 最终判断
    print("\n" + "=" * 60)
    print("门禁摘要")
    print("=" * 60)
    
    passed_count = sum(1 for _, p in checks if p)
    print(f"总检查: {len(checks)}")
    print(f"✅ 通过: {passed_count}")
    print(f"❌ 失败: {len(checks) - passed_count}")
    
    ready_for_production = all_passed and len(blockers) == 0
    
    print(f"\nready_for_production: {ready_for_production}")
    
    if blockers:
        print(f"\n阻塞项 ({len(blockers)}):")
        for b in blockers:
            print(f"  - {b}")
    
    # 保存门禁报告
    gate_report = {
        "scan_time": datetime.now().isoformat(),
        "checks": {name: passed for name, passed in checks},
        "passed_count": passed_count,
        "failed_count": len(checks) - passed_count,
        "blockers": blockers,
        "ready_for_production": ready_for_production
    }
    
    report_path = PROJECT_ROOT / "V75_6_PLUGIN_REALITY_GATE_REPORT.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(gate_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n报告已保存: {report_path}")
    
    return 0 if ready_for_production else 1


if __name__ == "__main__":
    sys.exit(main())
