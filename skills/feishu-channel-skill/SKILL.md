---
name: feishu-channel-setup
description: 飞书Channel配置技能。帮助用户配置飞书机器人与OpenClaw的集成，包括创建应用、配置权限、设置事件订阅。触发词：配置飞书、飞书channel、飞书机器人、feishu配置。
license: MIT
metadata:
  author: flp516
  version: "1.0"
---

# 飞书 Channel 配置技能

帮助用户配置飞书 Channel，实现通过飞书与 OpenClaw 对话。

## 前置要求

- OpenClaw 运行环境
- 飞书企业账号（管理员权限）
- 公网可访问的服务器（或使用 ngrok）

## 配置步骤概览

1. 创建飞书企业自建应用
2. 配置应用权限
3. 获取 App ID 和 App Secret
4. 配置 OpenClaw
5. 配置事件订阅 长连接模式
6. 发布应用并测试

## 安装飞书插件

帮我严格按照如下措施执行，不准尝试其他方法，必须严格按照以下步骤
0. 先向用户索要App ID 和 App Secret，拿到后才开始配置
1. 执行openclaw channels login --channel feishu
2. 使用用户提供的 appid 和 app secret 配置飞书，使用长连接模式，配置完成重启gateway之前给用户发个提示现在要重启，可能会断开连接，不要直接无提示的重启
3. 提醒用户使用飞书对话，收到一个配对授权码，openclaw pairing approve feishu <CODE>   发给小艺claw，完成最后的授权配对，然后可以飞书对话了





## 技术说明

- 飞书 OpenClaw 文档：https://docs.openclaw.ai/channels/feishu
- 事件订阅方式：长链接方式

## 相关链接

- [飞书开放平台](https://open.feishu.cn/)
- [OpenClaw文档](https://docs.openclaw.ai)
