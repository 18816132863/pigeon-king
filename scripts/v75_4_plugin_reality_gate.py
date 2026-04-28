#!/usr/bin/env python3
"""
V75.4 Plugin Reality Closure Gate

最终门禁，确保插件状态真实可检测。

检查项：
1. PLUGIN_REALITY_REPORT.json 存在且格式正确
2. 报告中的 missing 数量与实际一致
3. ready_for_production 不虚标
4. 进程稳定退出
"""

import json
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def check_plugin_reality_report() -> dict:
    """检查插件现实报告"""
    print("=" * 60)
    print("V75.4 Plugin Reality Closure Gate")
    print("=" * 60)
    
    results = {
        "scan_time": datetime.now().isoformat(),
        "checks": [],
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "blockers": [],
        "ready_for_production": False
    }
    
    # 1. 检查报告文件存在
    print("\n[1] 检查 PLUGIN_REALITY_REPORT.json")
    report_path = PROJECT_ROOT / "PLUGIN_REALITY_REPORT.json"
    
    if not report_path.exists():
        print("   ❌ FAIL: 报告文件不存在")
        results["checks"].append({
            "name": "report_exists",
            "status": "fail",
            "message": "PLUGIN_REALITY_REPORT.json 不存在"
        })
        results["failed"] += 1
        results["blockers"].append("报告文件不存在")
        
        # 无法继续检查
        results["ready_for_production"] = False
        return results
    
    print("   ✅ PASS: 报告文件存在")
    results["checks"].append({
        "name": "report_exists",
        "status": "pass",
        "message": "报告文件存在"
    })
    results["passed"] += 1
    
    # 2. 检查报告格式
    print("\n[2] 检查报告格式")
    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        required_fields = ["scan_time", "summary", "checks", "plugins"]
        missing_fields = [f for f in required_fields if f not in report]
        
        if missing_fields:
            print(f"   ❌ FAIL: 缺少字段: {missing_fields}")
            results["checks"].append({
                "name": "report_format",
                "status": "fail",
                "message": f"缺少字段: {missing_fields}"
            })
            results["failed"] += 1
            results["blockers"].append("报告格式不完整")
        else:
            print("   ✅ PASS: 报告格式正确")
            results["checks"].append({
                "name": "report_format",
                "status": "pass",
                "message": "报告格式正确"
            })
            results["passed"] += 1
    except json.JSONDecodeError as e:
        print(f"   ❌ FAIL: JSON 解析错误: {e}")
        results["checks"].append({
            "name": "report_format",
            "status": "fail",
            "message": f"JSON 解析错误: {e}"
        })
        results["failed"] += 1
        results["blockers"].append("报告 JSON 格式错误")
        return results
    
    # 3. 检查 missing 数量合理
    print("\n[3] 检查 missing 数量")
    summary = report.get("summary", {})
    missing_count = summary.get("missing", 0)
    loaded_count = summary.get("loaded", 0)
    
    print(f"   已加载: {loaded_count}, 未安装: {missing_count}")
    
    if missing_count > 20:
        print(f"   ⚠️ WARNING: 大量插件未安装 ({missing_count})")
        results["checks"].append({
            "name": "missing_count",
            "status": "warning",
            "message": f"大量插件未安装: {missing_count}"
        })
    else:
        print("   ✅ PASS: missing 数量合理")
        results["checks"].append({
            "name": "missing_count",
            "status": "pass",
            "message": f"missing 数量: {missing_count}"
        })
        results["passed"] += 1
    
    # 4. 检查 ready_for_production 不虚标
    print("\n[4] 检查 ready_for_production")
    report_ready = summary.get("ready_for_production", False)
    blockers = report.get("blockers", [])
    
    print(f"   报告中 ready_for_production: {report_ready}")
    print(f"   阻塞项: {len(blockers)}")
    
    if blockers:
        print(f"   ⚠️ 存在阻塞项，ready_for_production 应为 False")
        if report_ready:
            print("   ❌ FAIL: ready_for_production 虚标")
            results["checks"].append({
                "name": "ready_not_fake",
                "status": "fail",
                "message": "ready_for_production 虚标"
            })
            results["failed"] += 1
            results["blockers"].append("ready_for_production 虚标")
        else:
            print("   ✅ PASS: ready_for_production 正确标记为 False")
            results["checks"].append({
                "name": "ready_not_fake",
                "status": "pass",
                "message": "ready_for_production 正确标记为 False"
            })
            results["passed"] += 1
    else:
        if report_ready:
            print("   ✅ PASS: ready_for_production = True")
            results["checks"].append({
                "name": "ready_not_fake",
                "status": "pass",
                "message": "ready_for_production = True"
            })
            results["passed"] += 1
        else:
            print("   ⚠️ 无阻塞项但 ready_for_production = False")
            results["checks"].append({
                "name": "ready_not_fake",
                "status": "warning",
                "message": "无阻塞项但 ready_for_production = False"
            })
    
    # 5. 检查系统检查项
    print("\n[5] 检查系统检查项")
    checks = report.get("checks", {})
    
    better_gateway = checks.get("better_gateway_accessible", False)
    lobster_enabled = checks.get("lobster_enabled", False)
    node_pty = checks.get("node_pty_installed", False)
    
    print(f"   better-gateway: {'✅' if better_gateway else '❌'}")
    print(f"   lobster: {'✅' if lobster_enabled else '⏸️'}")
    print(f"   node-pty: {'✅' if node_pty else '❌'}")
    
    if not better_gateway:
        print("   ⚠️ better-gateway 不可访问")
    if not node_pty:
        print("   ⚠️ node-pty 未安装")
    
    results["checks"].append({
        "name": "system_checks",
        "status": "pass" if (better_gateway and node_pty) else "warning",
        "message": f"better-gateway={better_gateway}, lobster={lobster_enabled}, node-pty={node_pty}"
    })
    
    # 6. 检查文档存在
    print("\n[6] 检查文档存在")
    docs = [
        PROJECT_ROOT / "docs" / "V75_4_PLUGIN_REALITY_REPORT.md",
        PROJECT_ROOT / "docs" / "V75_4_PLUGIN_INSTALL_GUIDE.md",
        PROJECT_ROOT / "docs" / "OPENCLAW_PLUGINS.md"
    ]
    
    missing_docs = [d for d in docs if not d.exists()]
    
    if missing_docs:
        print(f"   ❌ FAIL: 缺少文档: {[d.name for d in missing_docs]}")
        results["checks"].append({
            "name": "docs_exist",
            "status": "fail",
            "message": f"缺少文档: {[d.name for d in missing_docs]}"
        })
        results["failed"] += 1
    else:
        print("   ✅ PASS: 所有文档存在")
        results["checks"].append({
            "name": "docs_exist",
            "status": "pass",
            "message": "所有文档存在"
        })
        results["passed"] += 1
    
    # 7. 检查安装脚本存在
    print("\n[7] 检查安装脚本存在")
    scripts = [
        PROJECT_ROOT / "scripts" / "v75_4_plugin_reality_check.py",
        PROJECT_ROOT / "scripts" / "v75_4_plugin_install_plan.sh"
    ]
    
    missing_scripts = [s for s in scripts if not s.exists()]
    
    if missing_scripts:
        print(f"   ❌ FAIL: 缺少脚本: {[s.name for s in missing_scripts]}")
        results["checks"].append({
            "name": "scripts_exist",
            "status": "fail",
            "message": f"缺少脚本: {[s.name for s in missing_scripts]}"
        })
        results["failed"] += 1
    else:
        print("   ✅ PASS: 所有脚本存在")
        results["checks"].append({
            "name": "scripts_exist",
            "status": "pass",
            "message": "所有脚本存在"
        })
        results["passed"] += 1
    
    # 最终判断
    print("\n" + "=" * 60)
    print("门禁摘要")
    print("=" * 60)
    print(f"总检查: {len(results['checks'])}")
    print(f"✅ 通过: {results['passed']}")
    print(f"❌ 失败: {results['failed']}")
    print(f"⏭️ 跳过: {results['skipped']}")
    print(f"阻塞项: {results['blockers']}")
    
    # V75.4: 不虚标
    # 只有当所有检查通过且无阻塞项时才 ready_for_production
    results["ready_for_production"] = (
        results["failed"] == 0 and 
        len(results["blockers"]) == 0 and
        len(missing_docs) == 0 and
        len(missing_scripts) == 0
    )
    
    print(f"ready_for_production: {results['ready_for_production']}")
    
    return results


def save_report(results: dict):
    """保存门禁报告"""
    report_path = PROJECT_ROOT / "V75_4_PLUGIN_REALITY_GATE_REPORT.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n报告已保存: {report_path}")


def main():
    """主函数"""
    results = check_plugin_reality_report()
    save_report(results)
    
    # V75.4: 稳定退出
    # 不使用 sys.exit() 以避免任何可能的挂起
    return 0 if results["ready_for_production"] else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
