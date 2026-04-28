#!/usr/bin/env python3
"""
V75.4 Plugin Reality Check

检查 OpenClaw 插件的真实安装状态。
不假装已安装，明确标记 missing。

检查项：
1. 推荐插件是否真实安装
2. better-gateway 路由是否可访问
3. lobster 工具是否可用
4. node-pty 是否安装
"""

import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional


class PluginStatus(str, Enum):
    LOADED = "loaded"
    DISABLED = "disabled"
    MISSING = "missing"
    UNKNOWN = "unknown"


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    plugin_id: str
    expected_source: str  # stock, npm, global
    status: PluginStatus
    version: Optional[str] = None
    source: Optional[str] = None
    description: Optional[str] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class PluginRealityReport:
    """插件现实检测报告"""
    scan_time: str
    total_checked: int
    loaded_count: int
    disabled_count: int
    missing_count: int
    plugins: List[PluginInfo]
    better_gateway_accessible: bool
    lobster_enabled: bool
    node_pty_installed: bool
    ready_for_production: bool
    blockers: List[str]


# 推荐插件清单
RECOMMENDED_PLUGINS = [
    # 开发工具类
    {"name": "commit-guard", "source": "npm", "description": "推送前拦截密钥"},
    {"name": "dep-audit", "source": "npm", "description": "漏洞扫描"},
    {"name": "pr-review", "source": "npm", "description": "AI 代码差异摘要"},
    {"name": "docker-helper", "source": "npm", "description": "Docker 日志查看"},
    {"name": "api-tester", "source": "npm", "description": "API 测试"},
    {"name": "git-stats", "source": "npm", "description": "代码库热点"},
    {"name": "todo-scanner", "source": "npm", "description": "TODO 扫描"},
    {"name": "changelog-gen", "source": "npm", "description": "更新日志生成"},
    {"name": "file-metrics", "source": "npm", "description": "代码复杂度"},
    
    # 记忆类
    {"name": "cortex-memory", "source": "npm", "description": "分层记忆"},
    {"name": "memory-lancedb", "source": "stock", "plugin_id": "memory-lancedb", "description": "LanceDB 记忆"},
    {"name": "lossless-claw", "source": "npm", "description": "防止上下文丢失"},
    {"name": "openclaw-engram", "source": "npm", "description": "本地记忆存储"},
    
    # 集成类
    {"name": "composio", "source": "npm", "description": "860+ 工具集成"},
    
    # 安全类
    {"name": "env-guard", "source": "npm", "description": "密钥打码"},
    {"name": "clawsec", "source": "npm", "description": "安全套件"},
    {"name": "secureclaw", "source": "npm", "description": "OWASP 检查"},
    
    # 可观测性与成本类
    {"name": "cost-tracker", "source": "npm", "description": "成本追踪"},
    {"name": "manifest", "source": "npm", "description": "模型路由"},
    {"name": "openclaw-observatory", "source": "npm", "description": "使用仪表板"},
    
    # 多智能体与元类
    {"name": "openclaw-foundry", "source": "npm", "description": "自动创建工具"},
    {"name": "claude-code-bridge", "source": "npm", "description": "Claude Code 桥接"},
    
    # 实用工具类
    {"name": "openclaw-better-gateway", "source": "npm", "package": "@thisisjeron/openclaw-better-gateway", "description": "增强网关"},
    {"name": "openclaw-ntfy", "source": "npm", "description": "手机通知"},
    {"name": "openclaw-sentry-tools", "source": "npm", "description": "Sentry 集成"},
    
    # Lobster (stock)
    {"name": "lobster", "source": "stock", "plugin_id": "lobster", "description": "工作流运行时"},
]


def get_installed_plugins() -> Dict[str, Dict]:
    """获取已安装插件列表"""
    result = subprocess.run(
        ["openclaw", "plugins", "list", "--json"],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        # 尝试解析非 JSON 输出
        return parse_plugins_list_output(result.stdout)
    
    try:
        data = json.loads(result.stdout)
        return {p["id"]: p for p in data.get("plugins", [])}
    except json.JSONDecodeError:
        return parse_plugins_list_output(result.stdout)


def parse_plugins_list_output(output: str) -> Dict[str, Dict]:
    """解析 openclaw plugins list 的表格输出"""
    plugins = {}
    
    for line in output.split('\n'):
        # 跳过分隔线和表头
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


def check_node_pty() -> bool:
    """检查 node-pty 是否安装"""
    result = subprocess.run(
        ["npm", "list", "@lydell/node-pty"],
        capture_output=True,
        text=True,
        timeout=10
    )
    return "@lydell/node-pty" in result.stdout and "empty" not in result.stdout


def check_better_gateway() -> bool:
    """检查 better-gateway 路由"""
    import urllib.request
    import urllib.error
    
    try:
        req = urllib.request.Request("http://localhost:18800/better-gateway/")
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except:
        return False


def check_lobster_enabled(installed_plugins: Dict) -> bool:
    """检查 lobster 是否启用"""
    if "lobster" in installed_plugins:
        return installed_plugins["lobster"].get("status") == "loaded"
    return False


def check_plugin_reality() -> PluginRealityReport:
    """检查插件现实状态"""
    print("=" * 60)
    print("V75.4 Plugin Reality Check")
    print("=" * 60)
    
    installed_plugins = get_installed_plugins()
    
    print(f"\n已发现 {len(installed_plugins)} 个插件")
    
    plugins_info = []
    loaded_count = 0
    disabled_count = 0
    missing_count = 0
    blockers = []
    
    print("\n检查推荐插件:")
    print("-" * 60)
    
    for rec in RECOMMENDED_PLUGINS:
        name = rec["name"]
        expected_source = rec["source"]
        plugin_id = rec.get("plugin_id", name.replace("-", "").replace("_", ""))
        description = rec.get("description", "")
        
        # 查找插件
        found = None
        for pid, pinfo in installed_plugins.items():
            if plugin_id in pid or pid in plugin_id or name.replace("-", "") in pinfo.get("name", "").replace("-", "").replace(" ", ""):
                found = pinfo
                break
        
        if found:
            status = PluginStatus.LOADED if found.get("status") == "loaded" else PluginStatus.DISABLED
            if status == PluginStatus.LOADED:
                loaded_count += 1
                symbol = "✅"
            else:
                disabled_count += 1
                symbol = "⏸️"
            
            plugin_info = PluginInfo(
                name=name,
                plugin_id=found.get("id", plugin_id),
                expected_source=expected_source,
                status=status,
                version=found.get("version"),
                source=found.get("source"),
                description=description
            )
            
            print(f"{symbol} {name}: {status.value} (v{found.get('version', '?')})")
        else:
            status = PluginStatus.MISSING
            missing_count += 1
            symbol = "❌"
            
            plugin_info = PluginInfo(
                name=name,
                plugin_id=plugin_id,
                expected_source=expected_source,
                status=status,
                description=description,
                notes=[f"未安装，预期来源: {expected_source}"]
            )
            
            print(f"{symbol} {name}: MISSING (预期: {expected_source})")
        
        plugins_info.append(plugin_info)
    
    # 检查 better-gateway
    print("\n" + "-" * 60)
    print("检查 better-gateway:")
    better_gateway_accessible = check_better_gateway()
    if better_gateway_accessible:
        print("✅ /better-gateway/ 路由可访问")
    else:
        print("❌ /better-gateway/ 路由不可访问")
        blockers.append("better-gateway 不可访问")
    
    # 检查 node-pty
    print("\n检查 node-pty:")
    node_pty_installed = check_node_pty()
    if node_pty_installed:
        print("✅ @lydell/node-pty 已安装")
    else:
        print("❌ @lydell/node-pty 未安装（终端功能不可用）")
        blockers.append("node-pty 未安装")
    
    # 检查 lobster
    print("\n检查 lobster:")
    lobster_enabled = check_lobster_enabled(installed_plugins)
    if lobster_enabled:
        print("✅ lobster 已启用")
    else:
        print("⏸️ lobster 存在但未启用")
    
    # 判断生产就绪
    # V75.4: 不虚标，只有真正安装的才算
    critical_missing = [
        p.name for p in plugins_info 
        if p.status == PluginStatus.MISSING and p.expected_source == "stock"
    ]
    
    if critical_missing:
        blockers.append(f"关键插件缺失: {', '.join(critical_missing)}")
    
    ready_for_production = len(blockers) == 0 and missing_count < len(RECOMMENDED_PLUGINS) // 2
    
    print("\n" + "=" * 60)
    print("检测摘要")
    print("=" * 60)
    print(f"总检查: {len(plugins_info)}")
    print(f"✅ 已加载: {loaded_count}")
    print(f"⏸️ 已禁用: {disabled_count}")
    print(f"❌ 未安装: {missing_count}")
    print(f"阻塞项: {len(blockers)}")
    print(f"ready_for_production: {ready_for_production}")
    
    return PluginRealityReport(
        scan_time=datetime.now().isoformat(),
        total_checked=len(plugins_info),
        loaded_count=loaded_count,
        disabled_count=disabled_count,
        missing_count=missing_count,
        plugins=plugins_info,
        better_gateway_accessible=better_gateway_accessible,
        lobster_enabled=lobster_enabled,
        node_pty_installed=node_pty_installed,
        ready_for_production=ready_for_production,
        blockers=blockers
    )


def generate_json_report(report: PluginRealityReport) -> str:
    """生成 JSON 报告"""
    data = {
        "scan_time": report.scan_time,
        "summary": {
            "total_checked": report.total_checked,
            "loaded": report.loaded_count,
            "disabled": report.disabled_count,
            "missing": report.missing_count,
            "ready_for_production": report.ready_for_production
        },
        "checks": {
            "better_gateway_accessible": report.better_gateway_accessible,
            "lobster_enabled": report.lobster_enabled,
            "node_pty_installed": report.node_pty_installed
        },
        "blockers": report.blockers,
        "plugins": [
            {
                "name": p.name,
                "plugin_id": p.plugin_id,
                "expected_source": p.expected_source,
                "status": p.status.value,
                "version": p.version,
                "source": p.source,
                "description": p.description,
                "notes": p.notes
            }
            for p in report.plugins
        ]
    }
    return json.dumps(data, indent=2, ensure_ascii=False)


def generate_markdown_report(report: PluginRealityReport) -> str:
    """生成 Markdown 报告"""
    lines = [
        "# V75.4 Plugin Reality Report",
        "",
        f"**扫描时间**: {report.scan_time}",
        "",
        "## 摘要",
        "",
        "| 指标 | 数值 |",
        "|------|------|",
        f"| 总检查 | {report.total_checked} |",
        f"| ✅ 已加载 | {report.loaded_count} |",
        f"| ⏸️ 已禁用 | {report.disabled_count} |",
        f"| ❌ 未安装 | {report.missing_count} |",
        f"| ready_for_production | {report.ready_for_production} |",
        "",
        "## 系统检查",
        "",
        f"- better-gateway 路由: {'✅ 可访问' if report.better_gateway_accessible else '❌ 不可访问'}",
        f"- lobster 启用状态: {'✅ 已启用' if report.lobster_enabled else '⏸️ 未启用'}",
        f"- node-pty 安装: {'✅ 已安装' if report.node_pty_installed else '❌ 未安装'}",
        "",
    ]
    
    if report.blockers:
        lines.extend([
            "## 阻塞项",
            "",
        ])
        for b in report.blockers:
            lines.append(f"- {b}")
        lines.append("")
    
    lines.extend([
        "## 插件详情",
        "",
        "| 名称 | 状态 | 版本 | 来源 | 说明 |",
        "|------|------|------|------|------|",
    ])
    
    for p in report.plugins:
        status_icon = "✅" if p.status == PluginStatus.LOADED else ("⏸️" if p.status == PluginStatus.DISABLED else "❌")
        lines.append(f"| {p.name} | {status_icon} {p.status.value} | {p.version or '-'} | {p.source or p.expected_source} | {p.description or ''} |")
    
    return "\n".join(lines)


def main():
    """主函数"""
    report = check_plugin_reality()
    
    # 保存 JSON 报告
    json_report = generate_json_report(report)
    json_path = Path(__file__).parent.parent / "PLUGIN_REALITY_REPORT.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(json_report)
    print(f"\nJSON 报告已保存: {json_path}")
    
    # 保存 Markdown 报告
    md_report = generate_markdown_report(report)
    md_path = Path(__file__).parent.parent / "docs" / "V75_4_PLUGIN_REALITY_REPORT.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_report)
    print(f"Markdown 报告已保存: {md_path}")
    
    # 返回码
    return 0 if report.ready_for_production else 1


if __name__ == "__main__":
    sys.exit(main())
