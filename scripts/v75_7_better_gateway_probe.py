#!/usr/bin/env python3
"""
V75.7 Better Gateway Probe - 专门检测 better-gateway
"""

import json
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path


def run_cmd(cmd, timeout=30):
    """运行命令"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def probe_better_gateway():
    """探测 better-gateway"""
    print("=" * 60)
    print("V75.7 Better Gateway Probe")
    print("=" * 60)
    
    result = {
        "scan_time": datetime.now().isoformat(),
        "checks": {},
        "runtime_verified": False,
        "blockers": []
    }
    
    # 1. 检查是否安装
    print("\n[1] 检查 openclaw-better-gateway 是否安装...")
    code, stdout, stderr = run_cmd(["openclaw", "plugins", "inspect", "openclaw-better-gateway"])
    installed = code == 0
    result["checks"]["installed"] = installed
    
    if installed:
        print("   ✅ 已安装")
    else:
        print("   ❌ 未安装")
        result["blockers"].append("openclaw-better-gateway 未安装")
    
    # 2. 检查是否启用
    print("\n[2] 检查是否启用...")
    enabled = False
    if installed:
        # 从 plugins list 中检查状态
        code, stdout, _ = run_cmd(["openclaw", "plugins", "list"])
        for line in stdout.split('\n'):
            if 'better-gateway' in line.lower() or 'openclaw-better-gateway' in line:
                if 'loaded' in line:
                    enabled = True
                    break
    
    result["checks"]["enabled"] = enabled
    
    if enabled:
        print("   ✅ 已启用")
    else:
        print("   ❌ 未启用")
        result["blockers"].append("openclaw-better-gateway 未启用")
    
    # 3. 检查路由是否可访问
    print("\n[3] 检查 /better-gateway/ 路由...")
    route_accessible = False
    try:
        req = urllib.request.Request("http://localhost:18800/better-gateway/")
        with urllib.request.urlopen(req, timeout=5) as response:
            route_accessible = response.status == 200
    except:
        pass
    
    result["checks"]["route_accessible"] = route_accessible
    
    if route_accessible:
        print("   ✅ 路由可访问")
    else:
        print("   ❌ 路由不可访问")
        result["blockers"].append("/better-gateway/ 路由不可访问")
    
    # 4. 检查 node-pty
    print("\n[4] 检查 @lydell/node-pty...")
    code, stdout, _ = run_cmd(["npm", "list", "-g", "@lydell/node-pty"])
    node_pty_available = "@lydell/node-pty" in stdout and "empty" not in stdout
    
    result["checks"]["node_pty_available"] = node_pty_available
    
    if node_pty_available:
        print("   ✅ node-pty 已安装")
    else:
        print("   ❌ node-pty 未安装")
        result["blockers"].append("@lydell/node-pty 未安装")
    
    # 5. 检查终端依赖
    print("\n[5] 检查终端依赖...")
    terminal_deps_available = node_pty_available  # 简化检查
    result["checks"]["terminal_deps_available"] = terminal_deps_available
    
    if terminal_deps_available:
        print("   ✅ 终端依赖可用")
    else:
        print("   ❌ 终端依赖不可用")
    
    # 运行时验证
    result["runtime_verified"] = (
        installed and 
        enabled and 
        route_accessible and 
        node_pty_available
    )
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("检测摘要")
    print("=" * 60)
    for check, passed in result["checks"].items():
        icon = "✅" if passed else "❌"
        print(f"{icon} {check}: {passed}")
    
    print(f"\nruntime_verified: {result['runtime_verified']}")
    
    if result["blockers"]:
        print(f"\n阻塞项 ({len(result['blockers'])}):")
        for b in result["blockers"]:
            print(f"  - {b}")
    
    # 保存报告
    report_path = Path(__file__).parent.parent / "V75_7_BETTER_GATEWAY_PROBE_REPORT.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n报告已保存: {report_path}")
    
    return 0 if result["runtime_verified"] else 1


if __name__ == "__main__":
    sys.exit(probe_better_gateway())
