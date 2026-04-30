---
name: weibo-clawbot-setup
description: 安装和配置微博 ClawBot 插件（Weibo OpenClaw Plugin）。当用户要求安装微博插件、配置微博 ClawBot、设置微博 OpenClaw 插件时使用此技能。支持从 Gitee 安装官方插件、配置 AppId/AppSecret 凭证、验证连接状态。
---

# 微博 ClawBot 安装配置指南

## 概述

微博 ClawBot 是微博官方推出的 OpenClaw 插件，支持通过微博私信与 ClawBot 对话，以及调用微博相关工具（热搜、智搜、用户微博等）。

### 步骤 ：配置凭证

1. 打开微博客户端，私信 **@微博龙虾助手**（用户ID：6808810981）
2. 发送消息：`连接龙虾`
3. 收到回复后，获取 `AppId` 和 `AppSecret`

## 安装流程


帮我严格按照如下措施执行，不准尝试其他方法，必须严格按照以下步骤
注意：先让用户提供`AppId` 和 `AppSecret`，拿到后再开始下面的安装步骤

0. 配置环境变量并让变量生效OPENCLAW_CLAWHUB_URL=https://cn.clawhub-mirror.com
1. export npm_config_maxsockets=1和export npm_config_concurrency=1
2. 执行 npm pack @wecode-ai/weibo-openclaw-plugin
3. 执行NPM_CONFIG_REGISTRY=https://registry.npmmirror.com openclaw plugins install '<刚才npm下载的文件>'



配置凭证：

```bash
openclaw config set 'channels.weibo.appId' '<your-appId>'
openclaw config set 'channels.weibo.appSecret' '<your-appSecret>'
```

### 步骤 5：重启 Gateway（重要：重启前一定要提示用户要重启了，连接可能会断开，不要直接就重启了）

```bash
openclaw gateway restart
```

### 步骤 6：验证安装

```bash
openclaw status
```

确认输出中 `Weibo` 显示 `ON · OK · configured`。

## 内置工具

安装成功后，以下工具可用：

| 工具名称 | 功能说明 |
|---------|---------|
| `weibo_token` | 获取微博 API 访问令牌 |
| `weibo_search` | 微博智搜，关键词搜索微博内容 |
| `weibo_status` | 获取用户发布的微博列表 |
| `weibo_hot_search` | 获取微博热搜榜 |
| `weibo_crowd` | 微博超话发帖工具 |




## 常见问题

### Q: 插件安装后显示 "unloaded"

检查凭证是否正确配置：
```bash
openclaw config get channels.weibo
```

