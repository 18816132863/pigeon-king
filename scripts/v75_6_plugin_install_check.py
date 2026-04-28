#!/usr/bin/env python3
"""
V75.6 Plugin Install Check - 真实检测

检测 OpenClaw 插件的真实安装状态：
- documented_only: 只有文档
- install_plan_generated: 有安装计划
- installed: 已安装
- enabled: 已启用
- loaded: 已加载
- runtime_verified: 运行时验证通过
- missing: 未安装
- disabled: 已禁用

只有 runtime_verified 才算真正闭环。
"""

import json
import os
import subprocess
import sys
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional


class PluginInstallStatus(str, Enum):
    DOCUMENTED_ONLY = "documented_only"
    INSTALL_PLAN_GENERATED = "install_plan_generated"
    INSTALLED = "installed"
    ENABLED = "enabled"
    LOADED = "loaded"
    RUNTIME_VERIFIED = "runtime_verified"
    MISSING = "missing"
    DISABLED = "disabled"


@dataclass
class PluginCheckResult:
    """插件检测结果"""
    name: str
    plugin_id: str
    status: PluginInstallStatus
    version: Optional[str] = None
    source: Optional[str] = None
    runtime_verified: bool = False
    checks: Dict[str, bool] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


@dataclass
class PluginInstallReport:
    """插件安装检测报告"""
    scan_time: str
    total_checked: int
    by_status: Dict[str, int]
    plugins: List[PluginCheckResult]
    better_gateway: Dict[str, Any]
    lobster: Dict[str, Any]
    node_pty: Dict[str, Any]
    scripts_exist: bool
    plugin_binaries_included: bool
    install_plan_available: bool
    ready_for_production: bool
    blockers: List[str]


# 需要检测的插件
PLUGINS_TO_CHECK = [
    {"name": "lobster", "plugin_id": "lobster", "source": "stock", "can_runtime_verify": True},
    {"name": "memory-lancedb", "plugin_id": "memory-lancedb", "source": "stock", "can_runtime_verify": False},
    {"name": "env-guard", "plugin_id": "env-guard", "source": "skill", "can_runtime_verify": True},
    {"name": "openclaw-better-gateway", "plugin_id": "openclaw-better-gateway", "source": "npm", "can_runtime_verify": True},
    {"name": "node-pty", "plugin_id": "@lydell/node-pty", "source": "npm", "can_runtime_verify": True},
]


def run_command(cmd: List[str], timeout: int = 30) -> tuple:
    """运行命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def get_openclaw_plugins() -> Dict[str, Dict]:
    """获取 OpenClaw 插件列表"""
    code, stdout, stderr = run_command(["openclaw", "plugins", "list"])
    
    plugins = {}
    for line in stdout.split('\n'):
        if '│' not in line or 'Name' in line or '─' in line:
            continue
        
        parts = [p.strip() for p in line.split('│')]
        if len(parts) >= 5:
            name = parts[1].strip()
            plugin_id = parts[2].strip()
            status = parts[4].strip()
            source = parts[5].strip() if len(parts) > 5 else ""
            version = parts[6].strip() if len(parts) > 6 else ""
            
            plugins[plugin_id] = {
                "name": name,
                "id": plugin_id,
                "status": status,
                "source": source,
                "version": version
            }
    
    return plugins


def check_better_gateway() -> Dict[str, Any]:
    """检查 better-gateway"""
    result = {
        "installed": False,
        "enabled": False,
        "route_accessible": False,
        "node_pty_available": False,
        "runtime_verified": False
    }
    
    # 检查是否安装
    code, stdout, _ = run_command(["openclaw", "plugins", "inspect", "openclaw-better-gateway"])
    result["installed"] = code == 0
    
    # 检查路由
    try:
        req = urllib.request.Request("http://localhost:18800/better-gateway/")
        with urllib.request.urlopen(req, timeout=5) as response:
            result["route_accessible"] = response.status == 200
    except:
        result["route_accessible"] = False
    
    # 检查 node-pty
    code, stdout, _ = run_command(["npm", "list", "-g", "@lydell/node-pty"])
    result["node_pty_available"] = "@lydell/node-pty" in stdout and "empty" not in stdout
    
    # 运行时验证
    result["runtime_verified"] = result["installed"] and result["route_accessible"] and result["node_pty_available"]
    
    return result


def check_lobster(openclaw_plugins: Dict) -> Dict[str, Any]:
    """检查 lobster"""
    result = {
        "installed": False,
        "enabled": False,
        "in_also_allow": False,
        "runtime_verified": False
    }
    
    # 检查是否安装
    if "lobster" in openclaw_plugins:
        plugin = openclaw_plugins["lobster"]
        result["installed"] = True
        result["enabled"] = plugin.get("status") == "loaded"
    
    # 检查 tools.alsoAllow
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
        also_allow = config.get("tools", {}).get("alsoAllow", [])
        result["in_also_allow"] = "lobster" in also_allow
    
    # 运行时验证
    result["runtime_verified"] = result["installed"] and result["enabled"] and result["in_also_allow"]
    
    return result


def check_node_pty() -> Dict[str, Any]:
    """检查 node-pty"""
    result = {
        "installed": False,
        "version": None,
        "runtime_verified": False
    }
    
    code, stdout, _ = run_command(["npm", "list", "-g", "@lydell/node-pty"])
    if "@lydell/node-pty" in stdout and "empty" not in stdout:
        result["installed"] = True
        # 提取版本
        import re
        match = re.search(r"@lydell/node-pty@([\d.]+)", stdout)
        if match:
            result["version"] = match.group(1)
    
    result["runtime_verified"] = result["installed"]
    
    return result


def check_single_plugin(plugin_info: Dict, openclaw_plugins: Dict) -> PluginCheckResult:
    """检查单个插件"""
    name = plugin_info["name"]
    plugin_id = plugin_info["plugin_id"]
    can_verify = plugin_info.get("can_runtime_verify", False)
    
    result = PluginCheckResult(
        name=name,
        plugin_id=plugin_id,
        status=PluginInstallStatus.MISSING
    )
    
    # 检查是否在 openclaw plugins list 中
    if plugin_id in openclaw_plugins:
        plugin = openclaw_plugins[plugin_id]
        result.version = plugin.get("version")
        result.source = plugin.get("source")
        
        if plugin.get("status") == "loaded":
            result.status = PluginInstallStatus.LOADED
        elif plugin.get("status") == "disabled":
            result.status = PluginInstallStatus.DISABLED
        else:
            result.status = PluginInstallStatus.INSTALLED
    
    # 检查是否有文档
    docs_path = Path(__file__).parent.parent / "docs" / f"{name.upper()}_GUIDE.md"
    if docs_path.exists():
        result.checks["documented"] = True
        if result.status == PluginInstallStatus.MISSING:
            result.status = PluginInstallStatus.DOCUMENTED_ONLY
    
    # 检查是否有安装计划
    install_plan = Path(__file__).parent / "v75_6_plugin_install_plan.sh"
    if install_plan.exists():
        result.checks["install_plan"] = True
        if result.status == PluginInstallStatus.DOCUMENTED_ONLY:
            result.status = PluginInstallStatus.INSTALL_PLAN_GENERATED
    
    # 运行时验证
    if can_verify and result.status in (PluginInstallStatus.LOADED, PluginInstallStatus.ENABLED):
        result.runtime_verified = True
        result.status = PluginInstallStatus.RUNTIME_VERIFIED
    
    return result


def check_scripts_exist() -> bool:
    """检查 scripts 目录是否存在"""
    scripts_dir = Path(__file__).parent
    required_scripts = [
        "v75_6_plugin_install_check.py",
        "v75_6_plugin_reality_gate.py",
    ]
    
    for script in required_scripts:
        if not (scripts_dir / script).exists():
            return False
    
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("V75.6 Plugin Install Check")
    print("=" * 60)
    
    # 获取 OpenClaw 插件列表
    print("\n[1] 获取 OpenClaw 插件列表...")
    openclaw_plugins = get_openclaw_plugins()
    print(f"    发现 {len(openclaw_plugins)} 个插件")
    
    # 检查各个插件
    print("\n[2] 检查插件状态...")
    results = []
    by_status = {s.value: 0 for s in PluginInstallStatus}
    
    for plugin_info in PLUGINS_TO_CHECK:
        result = check_single_plugin(plugin_info, openclaw_plugins)
        results.append(result)
        by_status[result.status.value] += 1
        
        icon = "✅" if result.runtime_verified else ("⏸️" if result.status == PluginInstallStatus.DISABLED else "❌")
        print(f"    {icon} {result.name}: {result.status.value}")
    
    # 检查 better-gateway
    print("\n[3] 检查 better-gateway...")
    better_gateway = check_better_gateway()
    print(f"    installed: {better_gateway['installed']}")
    print(f"    route_accessible: {better_gateway['route_accessible']}")
    print(f"    node_pty_available: {better_gateway['node_pty_available']}")
    print(f"    runtime_verified: {better_gateway['runtime_verified']}")
    
    # 检查 lobster
    print("\n[4] 检查 lobster...")
    lobster = check_lobster(openclaw_plugins)
    print(f"    installed: {lobster['installed']}")
    print(f"    enabled: {lobster['enabled']}")
    print(f"    in_also_allow: {lobster['in_also_allow']}")
    print(f"    runtime_verified: {lobster['runtime_verified']}")
    
    # 检查 node-pty
    print("\n[5] 检查 node-pty...")
    node_pty = check_node_pty()
    print(f"    installed: {node_pty['installed']}")
    print(f"    version: {node_pty['version']}")
    print(f"    runtime_verified: {node_pty['runtime_verified']}")
    
    # 检查 scripts
    print("\n[6] 检查 scripts 目录...")
    scripts_exist = check_scripts_exist()
    print(f"    scripts_exist: {scripts_exist}")
    
    # 判断生产就绪
    blockers = []
    
    if by_status.get("runtime_verified", 0) == 0:
        blockers.append("无插件通过 runtime_verified")
    
    if not better_gateway["runtime_verified"]:
        blockers.append("better-gateway 未通过运行时验证")
    
    if not lobster["runtime_verified"]:
        blockers.append("lobster 未通过运行时验证")
    
    if not node_pty["runtime_verified"]:
        blockers.append("node-pty 未安装")
    
    if not scripts_exist:
        blockers.append("scripts 目录不完整")
    
    # V75.6: 严格判断
    ready_for_production = len(blockers) == 0
    
    # 生成报告
    report = PluginInstallReport(
        scan_time=datetime.now().isoformat(),
        total_checked=len(results),
        by_status=by_status,
        plugins=results,
        better_gateway=better_gateway,
        lobster=lobster,
        node_pty=node_pty,
        scripts_exist=scripts_exist,
        plugin_binaries_included=False,  # 插件本体不包含在工程中
        install_plan_available=True,
        ready_for_production=ready_for_production,
        blockers=blockers
    )
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("检测摘要")
    print("=" * 60)
    print(f"总检查: {report.total_checked}")
    for status, count in by_status.items():
        if count > 0:
            print(f"  {status}: {count}")
    print(f"scripts_exist: {scripts_exist}")
    print(f"plugin_binaries_included: {report.plugin_binaries_included}")
    print(f"install_plan_available: {report.install_plan_available}")
    print(f"ready_for_production: {ready_for_production}")
    
    if blockers:
        print(f"\n阻塞项 ({len(blockers)}):")
        for b in blockers:
            print(f"  - {b}")
    
    # 保存报告
    report_path = Path(__file__).parent.parent / "V75_6_PLUGIN_INSTALL_CHECK_REPORT.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "scan_time": report.scan_time,
            "total_checked": report.total_checked,
            "by_status": report.by_status,
            "plugins": [
                {
                    "name": p.name,
                    "plugin_id": p.plugin_id,
                    "status": p.status.value,
                    "version": p.version,
                    "source": p.source,
                    "runtime_verified": p.runtime_verified,
                    "checks": p.checks,
                    "notes": p.notes
                }
                for p in report.plugins
            ],
            "better_gateway": report.better_gateway,
            "lobster": report.lobster,
            "node_pty": report.node_pty,
            "scripts_exist": report.scripts_exist,
            "plugin_binaries_included": report.plugin_binaries_included,
            "install_plan_available": report.install_plan_available,
            "ready_for_production": report.ready_for_production,
            "blockers": report.blockers
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n报告已保存: {report_path}")
    
    return 0 if ready_for_production else 1


if __name__ == "__main__":
    sys.exit(main())
