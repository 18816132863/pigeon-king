# V26 Timeout Resilience / 端侧工具超时治理版

## 解决的问题

端侧工具、Calendar、Gmail、设备执行器、大量操作容易卡在 60 秒超时。  
V26 把同步阻塞调用改成：

```text
fast ack
→ resumable job
→ chunked steps
→ heartbeat
→ checkpoint before timeout
→ retry/backoff
→ poll/resume
→ final report
```

## 默认入口

```python
yuanling_system.DefaultEntry = TopAIOperatorV26
```

## 核心策略

| 问题 | V26 处理 |
|---|---|
| 单次调用超过60秒 | 禁止长阻塞，拆成小步骤 |
| 端侧工具等待审批导致超时 | 审批等待不阻塞主调用 |
| Calendar/Gmail 大量读取 | fast ack + chunk + heartbeat |
| 设备动作 | approval_required + checkpoint |
| 执行中断 | 从 checkpoint 恢复 |
| 多次失败 | retry/backoff + 降级到 dry-run/draft |

## 执行命令

```bash
tar -xzf pigeon_king_v26_timeout_resilience_full_replace.tar.gz -C . && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v26_apply_timeout_resilience.py && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v26_verify_timeout_resilience.py
```

## 成功标志

```text
PASS: V26 Timeout Resilience verification passed.
```

## 验收重点

- 180秒长任务不能阻塞到60秒超时
- 必须拆分 step
- 必须产生 heartbeat
- 必须产生 checkpoint
- 必须可 resume
- 审批等待不能占用同步调用
- 仍然保留 V25 connector execution / memory writeback
