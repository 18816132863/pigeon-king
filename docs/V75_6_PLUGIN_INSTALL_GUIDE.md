# V75.6 Plugin Install Guide

本文档说明 V75.6 版本的插件安装状态和安装计划。

## 当前状态

| 插件 | 状态 | 说明 |
|------|------|------|
| lobster | ✅ runtime_verified | 已安装、已启用、已验证 |
| memory-lancedb | ❌ missing | 需要 OpenAI API Key |
| env-guard | ❌ missing | 需要安装 |
| openclaw-better-gateway | ❌ missing | 需要安装 |
| @lydell/node-pty | ❌ missing | 需要安装 |

## 生产就绪状态

**ready_for_production: False**

阻塞项：
- better-gateway 未通过运行时验证
- node-pty 未安装

## 安装计划

运行以下命令安装缺失的插件：

```bash
bash scripts/v75_6_plugin_install_plan.sh --execute
```

或手动安装：

```bash
# 启用 lobster（已启用）
openclaw plugins enable lobster

# 安装 env-guard
openclaw skills install env-guard

# 安装 node-pty
npm install -g @lydell/node-pty
```

## 插件本体说明

**plugin_binaries_included: False**

插件本体不包含在工程压缩包中，原因：
1. 插件体积较大（node_modules 等）
2. 插件需要根据环境动态安装
3. 部分插件需要外部依赖（如 OpenAI API Key）

工程中包含：
- 安装计划脚本
- 检测脚本
- 安装指南

## 检测脚本

| 脚本 | 功能 |
|------|------|
| `scripts/v75_6_plugin_install_check.py` | 检测插件安装状态 |
| `scripts/v75_6_plugin_reality_gate.py` | 最终门禁 |
| `scripts/v75_6_plugin_install_plan.sh` | 安装计划 |
| `scripts/v75_6_openclaw_plugin_probe.py` | OpenClaw 插件探测 |

## 运行检测

```bash
# 检测插件状态
python3 scripts/v75_6_plugin_install_check.py

# 运行门禁
python3 scripts/v75_6_plugin_reality_gate.py

# 探测 OpenClaw
python3 scripts/v75_6_openclaw_plugin_probe.py
```

## 状态定义

| 状态 | 说明 |
|------|------|
| documented_only | 只有文档，未安装 |
| install_plan_generated | 有安装计划 |
| installed | 已安装 |
| enabled | 已启用 |
| loaded | 已加载 |
| runtime_verified | 运行时验证通过 |
| missing | 未安装 |
| disabled | 已禁用 |

**只有 runtime_verified 才算真正闭环。**
