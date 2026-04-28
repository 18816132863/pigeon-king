#!/usr/bin/env python3
"""
V75.6 OpenClaw Plugin Probe - 探测 OpenClaw 插件系统
"""

import json
import subprocess
import sys
from pathlib import Path


def run_cmd(cmd):
    """运行命令"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def probe_openclaw_config():
    """探测 OpenClaw 配置"""
    print("=" * 60)
    print("OpenClaw 配置探测")
    print("=" * 60)
    
    config_path = Path.home() / ".openclaw" / "openclaw.json"
    
    if not config_path.exists():
        print("❌ 配置文件不存在")
        return None
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    print(f"✅ 配置文件存在: {config_path}")
    
    # 提取关键配置
    plugins_allow = config.get("plugins", {}).get("allow", [])
    tools_also_allow = config.get("tools", {}).get("alsoAllow", [])
    plugins_entries = config.get("plugins", {}).get("entries", {})
    skills_entries = config.get("skills", {}).get("entries", {})
    
    print(f"\nplugins.allow: {plugins_allow}")
    print(f"tools.alsoAllow: {tools_also_allow}")
    
    print(f"\n已启用插件:")
    for k, v in plugins_entries.items():
        if v.get("enabled"):
            print(f"  ✅ {k}")
    
    print(f"\n已启用技能:")
    for k, v in skills_entries.items():
        if v.get("enabled", True):
            print(f"  ✅ {k}")
    
    return config


def probe_plugins_list():
    """探测插件列表"""
    print("\n" + "=" * 60)
    print("OpenClaw 插件列表")
    print("=" * 60)
    
    code, stdout, stderr = run_cmd(["openclaw", "plugins", "list"])
    
    if code != 0:
        print(f"❌ 获取插件列表失败: {stderr}")
        return
    
    # 解析输出
    plugins = []
    for line in stdout.split('\n'):
        if '│' not in line or 'Name' in line or '─' in line:
            continue
        
        parts = [p.strip() for p in line.split('│')]
        if len(parts) >= 5:
            plugins.append({
                "name": parts[1],
                "id": parts[2],
                "status": parts[4]
            })
    
    loaded = [p for p in plugins if p["status"] == "loaded"]
    disabled = [p for p in plugins if p["status"] == "disabled"]
    
    print(f"\n已加载 ({len(loaded)}):")
    for p in loaded[:10]:
        print(f"  ✅ {p['name']} ({p['id']})")
    
    print(f"\n已禁用 ({len(disabled)}):")
    for p in disabled[:10]:
        print(f"  ⏸️ {p['name']} ({p['id']})")


def probe_specific_plugins():
    """探测特定插件"""
    print("\n" + "=" * 60)
    print("特定插件探测")
    print("=" * 60)
    
    # lobster
    print("\n[lobster]")
    code, stdout, _ = run_cmd(["openclaw", "plugins", "inspect", "lobster"])
    if code == 0:
        print("✅ lobster 已安装")
    else:
        print("❌ lobster 未安装")
    
    # memory-lancedb
    print("\n[memory-lancedb]")
    code, stdout, _ = run_cmd(["openclaw", "plugins", "inspect", "memory-lancedb"])
    if code == 0:
        print("✅ memory-lancedb 已安装")
    else:
        print("❌ memory-lancedb 未安装")


def main():
    """主函数"""
    probe_openclaw_config()
    probe_plugins_list()
    probe_specific_plugins()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
