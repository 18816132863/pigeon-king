# OpenClaw 插件推荐

## 开发工具类

| 插件 | 功能 |
|------|------|
| `commit-guard` | 推送前拦截密钥、超大文件、糟糕提交记录 |
| `dep-audit` | 一行命令漏洞扫描，支持多种技术栈 |
| `pr-review` | AI 生成代码差异摘要，提前发现问题 |
| `docker-helper` | 聊天界面内查看日志和容器状态 |
| `api-tester` | 聊天内调用接口，美化 JSON 输出 |
| `git-stats` | 展示代码库热点和贡献者信息 |
| `todo-scanner` | 扫描 TODO/FIXME 等待办事项 |
| `changelog-gen` | 根据提交信息自动生成更新日志 |
| `file-metrics` | 代码库复杂度快照 |

## 记忆类

| 插件 | 功能 |
|------|------|
| `cortex-memory` | 分层记忆机制，长时间会话稳定 |
| `memory-lancedb-pro` | 更好的记忆检索效果 |
| `lossless-claw` | 防止会话中途丢失上下文 |
| `openclaw-engram` | 完全本地的记忆存储，隐私优先 |

## 集成类

| 插件 | 功能 |
|------|------|
| `composio` | 连接 860+ 工具（Gmail、Slack、GitHub、Notion、Linear），OAuth 托管 |

## 安全类

| 插件 | 功能 |
|------|------|
| `env-guard` | 自动打码密钥和 API 令牌（最先安装！） |
| `clawsec` | 完整安全套件，捕捉提示词注入等攻击 |
| `secureclaw` | OWASP 风格安全检查 |

## 可观测性与成本类

| 插件 | 功能 |
|------|------|
| `cost-tracker` | 显示每个会话、每个模型的成本 |
| `manifest` | 自动路由到更便宜的模型 |
| `openclaw-observatory` | 使用情况和成本仪表板 |

## 多智能体与元类

| 插件 | 功能 |
|------|------|
| `openclaw-foundry` | 根据使用习惯自动创建新工具 |
| `claude-code-bridge` | 在 OpenClaw 内使用 Claude Code |

## 实用工具类

| 插件 | 功能 |
|------|------|
| `openclaw-better-gateway` | 增强网关路由、内嵌 IDE、嵌入式终端 |
| `openclaw-ntfy` | 长任务完成时手机通知 |
| `openclaw-sentry-tools` | 拉取 Sentry 错误信息到上下文 |

## Lobster - 类型化工作流运行时

**核心价值：**
- 多步工作流变成一条调用，节省 tokens
- 内置审批检查点，副作用前自动暂停
- 暂停/恢复执行，支持 resumeToken

**使用示例：**
```json
{
  "action": "run",
  "pipeline": "inbox-list | inbox-categorize | approve --prompt 'Apply changes?' | inbox-apply",
  "timeoutMs": 30000
}
```

## 推荐必装组合

```
env-guard → composio → cortex-memory → cost-tracker → commit-guard → openclaw-better-gateway
```

## 安装命令

```bash
# 安装 better-gateway
openclaw plugins install @thisisjeron/openclaw-better-gateway

# 安装 node-pty（终端支持）
npm i @lydell/node-pty
```
