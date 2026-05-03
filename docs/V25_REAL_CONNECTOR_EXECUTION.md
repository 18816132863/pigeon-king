# V25 Real Connector Execution / 真实连接器执行版

V24 已经完成顶层入口和真实工具绑定。V25 继续往前推：把 tool/capability 接入真实 connector 执行层。

## 主链

```text
收到消息
→ yuanling_system.DefaultEntry = TopAIOperatorV25
→ TopAIOperator
→ AIShapeCore
→ GoalContract
→ TaskGraph DAG
→ RealToolBinding
→ RealConnectorExecution
→ Connector Result
→ Checkpoint
→ Memory Writeback
→ Final Report
```

## 新增 connector

| Connector | 行为 |
|---|---|
| FileWorkspaceConnector | 真实写入本地安全 workspace artifact |
| MailDraftConnector | 只生成邮件草稿，不发送 |
| CalendarDraftConnector | 只生成日程草稿，不写外部日历 |
| SafeScriptConnector | 只执行 allowlist 安全脚本，否则审批 |
| ModelRouteConnector | 准备模型路由，不强制外部调用 |
| ActionBridgeConnector | 准备真实动作，等待审批 |
| DevicePrepareConnector | 准备设备动作，等待审批 |
| GenericConnector | 内部安全工具执行/预演 |

## 默认入口

```python
yuanling_system.DefaultEntry = TopAIOperatorV25
```

## 执行命令

```bash
tar -xzf pigeon_king_v25_real_connector_execution_full_replace.tar.gz -C . && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v25_apply_real_connector_execution.py && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v25_verify_real_connector_execution.py
```

## 成功标志

```text
PASS: V25 Real Connector Execution verification passed.
```

## 安全边界

- 文件 connector 只写本地 workspace artifact。
- 邮件/日程 connector 只 draft，不外发、不写外部系统。
- 脚本 connector 只执行 allowlist，否则审批。
- 设备/真实动作 connector 只 prepare，等待审批。
- token / api_key / 密钥 / 密码外泄直接 blocked。
