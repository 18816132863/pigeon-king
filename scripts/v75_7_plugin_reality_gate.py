#!/usr/bin/env python3
"""
V75.7 Plugin Reality Gate - 最终门禁

严格判断，不虚标。

规则：
1. 读取 V75_7_PLUGIN_INSTALL_CHECK_REPORT.json
2. 如果 ready_for_production=false，gate 也必须 false
3. 如果 blockers 非空，gate 也必须 false
4. 如果 better_gateway.runtime_verified=false，gate 也必须 false
5. 如果 lobster.runtime_verified=false，gate 也必须 false
6. 如果 node_pty.runtime_verified=false，gate 也必须 false
7. 报告口径必须一致
"""

import json
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


def check_install_check_report() -> dict:
    """检查安装检测报告"""
    print("\n[1] 检查 V75_7_PLUGIN_INSTALL_CHECK_REPORT.json")
    
    report_path = PROJECT_ROOT / "V75_7_PLUGIN_INSTALL_CHECK_REPORT.json"
    
    result = {
        "exists": False,
        "ready_for_production": False,
        "ready_for_controlled_test": True,
        "blockers": [],
        "passed": False
    }
    
    if not report_path.exists():
        print("   ❌ FAIL: 报告文件不存在")
        result["blockers"].append("V75_7_PLUGIN_INSTALL_CHECK_REPORT.json 不存在")
        return result
    
    result["exists"] = True
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    # V75.7: 直接读取报告中的状态
    result["ready_for_production"] = report.get("ready_for_production", False)
    result["ready_for_controlled_test"] = report.get("ready_for_controlled_test", True)
    result["blockers"] = report.get("blockers", [])
    
    # 检查 better_gateway
    bg = report.get("better_gateway", {})
    if not bg.get("runtime_verified", False):
        if "better-gateway 未通过运行时验证" not in result["blockers"]:
            result["blockers"].append("better-gateway 未通过运行时验证")
    
    # 检查 lobster
    lobster = report.get("lobster", {})
    if not lobster.get("runtime_verified", False):
        if "lobster 未通过运行时验证" not in result["blockers"]:
            result["blockers"].append("lobster 未通过运行时验证")
    
    # 检查 node_pty
    np = report.get("node_pty", {})
    if not np.get("runtime_verified", False):
        if "node-pty 未安装" not in result["blockers"]:
            result["blockers"].append("node-pty 未安装")
    
    # V75.7: 严格判断
    # 只有没有阻塞项才能 production ready
    result["passed"] = len(result["blockers"]) == 0
    
    if result["passed"]:
        print(f"   ✅ PASS: 无阻塞项")
    else:
        print(f"   ❌ FAIL: 存在阻塞项 ({len(result['blockers'])})")
        for b in result["blockers"]:
            print(f"      - {b}")
    
    return result


def check_better_gateway_probe() -> dict:
    """检查 better-gateway 探测报告"""
    print("\n[2] 检查 V75_7_BETTER_GATEWAY_PROBE_REPORT.json")
    
    report_path = PROJECT_ROOT / "V75_7_BETTER_GATEWAY_PROBE_REPORT.json"
    
    result = {
        "exists": False,
        "runtime_verified": False,
        "passed": False
    }
    
    if not report_path.exists():
        print("   ⚠️ WARNING: 报告文件不存在（需要运行 better_gateway_probe）")
        return result
    
    result["exists"] = True
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    result["runtime_verified"] = report.get("runtime_verified", False)
    result["passed"] = result["runtime_verified"]
    
    if result["passed"]:
        print(f"   ✅ PASS: better-gateway runtime_verified")
    else:
        print(f"   ❌ FAIL: better-gateway 未通过验证")
    
    return result


def check_lobster_probe() -> dict:
    """检查 lobster 探测报告"""
    print("\n[3] 检查 V75_7_LOBSTER_PROBE_REPORT.json")
    
    report_path = PROJECT_ROOT / "V75_7_LOBSTER_PROBE_REPORT.json"
    
    result = {
        "exists": False,
        "runtime_verified": False,
        "passed": False
    }
    
    if not report_path.exists():
        print("   ⚠️ WARNING: 报告文件不存在（需要运行 lobster_probe）")
        return result
    
    result["exists"] = True
    
    with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    result["runtime_verified"] = report.get("runtime_verified", False)
    result["passed"] = result["runtime_verified"]
    
    if result["passed"]:
        print(f"   ✅ PASS: lobster runtime_verified")
    else:
        print(f"   ❌ FAIL: lobster 未通过验证")
    
    return result


def check_reports_consistency() -> dict:
    """检查报告一致性"""
    print("\n[4] 检查报告口径一致性")
    
    result = {
        "consistent": True,
        "issues": []
    }
    
    # 读取所有报告
    reports = {}
    report_files = [
        "V75_7_PLUGIN_INSTALL_CHECK_REPORT.json",
        "V75_7_PLUGIN_REALITY_GATE_REPORT.json",
    ]
    
    for rf in report_files:
        rp = PROJECT_ROOT / rf
        if rp.exists():
            with open(rp, 'r') as f:
                reports[rf] = json.load(f)
    
    # 检查 ready_for_production 一致性
    ready_values = set()
    for rf, data in reports.items():
        if "ready_for_production" in data:
            ready_values.add(data["ready_for_production"])
    
    if len(ready_values) > 1:
        result["consistent"] = False
        result["issues"].append(f"ready_for_production 不一致: {ready_values}")
    
    if result["consistent"]:
        print("   ✅ PASS: 报告口径一致")
    else:
        print(f"   ❌ FAIL: {result['issues']}")
    
    return result


def main():
    """主函数"""
    print("=" * 60)
    print("V75.7 Plugin Reality Gate")
    print("=" * 60)
    
    # 1. 检查安装检测报告
    r1 = check_install_check_report()
    
    # 2. 检查 better-gateway 探测
    r2 = check_better_gateway_probe()
    
    # 3. 检查 lobster 探测
    r3 = check_lobster_probe()
    
    # 4. 检查报告一致性
    r4 = check_reports_consistency()
    
    # 最终判断
    print("\n" + "=" * 60)
    print("门禁摘要")
    print("=" * 60)
    
    # V75.7: 严格判断
    # 必须所有检查都通过
    all_blockers = list(r1.get("blockers", []))
    
    if r2.get("exists") and not r2.get("runtime_verified", False):
        all_blockers.append("better-gateway probe 未通过")
    
    if r3.get("exists") and not r3.get("runtime_verified", False):
        all_blockers.append("lobster probe 未通过")
    
    if not r4.get("consistent", True):
        all_blockers.append("报告口径不一致")
    
    # 最终状态
    ready_for_production = len(all_blockers) == 0
    ready_for_controlled_test = True  # 安装计划存在即可
    
    print(f"阻塞项: {len(all_blockers)}")
    if all_blockers:
        for b in all_blockers:
            print(f"  - {b}")
    
    print(f"\nready_for_production: {ready_for_production}")
    print(f"ready_for_controlled_test: {ready_for_controlled_test}")
    
    # 保存门禁报告
    gate_report = {
        "scan_time": datetime.now().isoformat(),
        "checks": {
            "install_check_report": r1.get("passed", False),
            "better_gateway_probe": r2.get("passed", False) if r2.get("exists") else None,
            "lobster_probe": r3.get("passed", False) if r3.get("exists") else None,
            "reports_consistency": r4.get("consistent", False)
        },
        "blockers": all_blockers,
        "ready_for_production": ready_for_production,
        "ready_for_controlled_test": ready_for_controlled_test
    }
    
    report_path = PROJECT_ROOT / "V75_7_PLUGIN_REALITY_GATE_REPORT.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(gate_report, f, indent=2, ensure_ascii=False)
    
    print(f"\n报告已保存: {report_path}")
    
    # V75.7: 返回码必须反映真实状态
    return 0 if ready_for_production else 1


if __name__ == "__main__":
    sys.exit(main())
