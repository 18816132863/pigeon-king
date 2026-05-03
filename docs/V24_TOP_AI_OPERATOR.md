# V24 Top AI Operator / 顶层实战总入口

这版是从 V23.2 继续往最顶层推进，不再分小版本。

## 主链

```text
收到消息
→ TopAIOperator / DefaultEntry
→ AIShapeCore
→ GoalContract
→ TaskGraph DAG
→ Constitution Judge
→ RealToolBinding
→ Tool Execution Result
→ Approval / Block / Real Safe Local
→ Checkpoint
→ Memory Writeback
→ Final Report
```

## 默认入口

- `yuanling_system.DefaultEntry = TopAIOperator`
- `core.top_ai_operator.TopAIOperator`
- `core.real_tool_binding.ToolBindingKernel`
- `scripts/top_ai_operator_main.py`

## 执行命令

```bash
tar -xzf pigeon_king_v24_top_ai_operator_full_replace.tar.gz -C . && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v24_apply_top_ai_operator.py && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v24_verify_top_ai_operator.py
```

## 成功标志

```text
PASS: V24 Top AI Operator verification passed.
```

## 验收内容

输入一句真实任务后，必须能看到：

1. GoalContract
2. TaskGraph DAG
3. 风险裁判结果
4. 每个节点绑定的 tool/capability
5. tool 执行模式：real / dry_run / approval_required / blocked
6. tool result
7. checkpoint
8. action log
9. memory writeback
10. final report

## 安全边界

- 内部安全工具可 real 执行：目标编译、记忆读写、法典裁判、checkpoint、报告。
- 外部发送、日程写入、设备控制、本地脚本、安装、删除、付款默认 approval_required。
- token / api_key / 密钥 / 密码外泄直接 blocked。
