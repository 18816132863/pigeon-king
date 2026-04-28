# V75.4 Plugin Install Guide

本文档说明如何在 OpenClaw 中安装和配置推荐插件。

## 前置条件

- OpenClaw 2026.3.24 或更高版本
- Node.js 18+ 和 npm
- 网络访问（用于下载插件）

## 快速安装

```bash
# 1. 安装 node-pty（终端支持）
npm install -g @lydell/node-pty

# 2. 安装 better-gateway
openclaw plugins install @thisisjeron/openclaw-better-gateway

# 3. 启用 lobster
openclaw plugins enable lobster
```

## 推荐插件清单

### 🔒 安全类（最先安装）

```bash
# 密钥打码 - 防止敏感信息泄露
openclaw plugins install env-guard

# 安全套件 - 捕捉提示词注入等攻击
openclaw plugins install clawsec

# OWASP 检查
openclaw plugins install secureclaw
```

### 🧠 记忆类

```bash
# 分层记忆
openclaw plugins install cortex-memory

# LanceDB 记忆（stock 插件，只需启用）
openclaw plugins enable memory-lancedb

# 防止上下文丢失
openclaw plugins install lossless-claw

# 本地记忆存储
openclaw plugins install openclaw-engram
```

### 🔗 集成类

```bash
# 860+ 工具集成（Gmail、Slack、GitHub、Notion、Linear）
openclaw plugins install composio
```

### 📊 可观测性与成本类

```bash
# 成本追踪
openclaw plugins install cost-tracker

# 模型路由优化
openclaw plugins install manifest

# 使用仪表板
openclaw plugins install openclaw-observatory
```

### 🛠️ 开发工具类

```bash
# 推送前检查
openclaw plugins install commit-guard

# 漏洞扫描
openclaw plugins install dep-audit

# PR 代码审查
openclaw plugins install pr-review

# Docker 辅助
openclaw plugins install docker-helper

# API 测试
openclaw plugins install api-tester

# Git 统计
openclaw plugins install git-stats

# TODO 扫描
openclaw plugins install todo-scanner

# 更新日志生成
openclaw plugins install changelog-gen

# 文件指标
openclaw plugins install file-metrics
```

### 🤖 多智能体与元类

```bash
# 自动创建工具
openclaw plugins install openclaw-foundry

# Claude Code 桥接
openclaw plugins install claude-code-bridge
```

### 📱 实用工具类

```bash
# 手机通知
openclaw plugins install openclaw-ntfy

# Sentry 集成
openclaw plugins install openclaw-sentry-tools
```

## Lobster 配置

Lobster 是内置的工作流运行时，需要在配置中启用：

```json
// ~/.openclaw/openclaw.json
{
  "tools": {
    "alsoAllow": ["lobster"]
  }
}
```

## Better Gateway 配置

安装后，better-gateway 会在 `/better-gateway/` 路径提供增强 UI：

- 内嵌 IDE（Monaco 编辑器）
- 嵌入式终端（需要 node-pty）
- 文件 API
- 快捷键支持

访问地址：`http://localhost:18800/better-gateway/`

## 验证安装

```bash
# 列出所有插件
openclaw plugins list

# 检查插件详情
openclaw plugins inspect <plugin-id>

# 运行插件诊断
openclaw plugins doctor
```

## 故障排除

### 插件加载失败

```bash
# 检查插件状态
openclaw plugins doctor

# 重新安装
openclaw plugins install <plugin> --force
```

### node-pty 安装失败

node-pty 需要编译原生模块：

```bash
# 安装编译工具
sudo apt-get install build-essential python3

# 重新安装
npm install -g @lydell/node-pty --build-from-source
```

### better-gateway 无法访问

1. 确认 OpenClaw Gateway 正在运行
2. 检查端口 18800 是否被占用
3. 确认插件已启用：`openclaw plugins enable openclaw-better-gateway`

## 插件状态说明

| 状态 | 含义 |
|------|------|
| `loaded` | 已加载并可用 |
| `disabled` | 已安装但未启用 |
| `missing` | 未安装 |

## 必装组合

推荐的最小安装组合：

```
env-guard → composio → cortex-memory → cost-tracker → commit-guard → openclaw-better-gateway
```

这组插件覆盖了安全、集成、记忆、成本、代码质量和开发体验的核心需求。
