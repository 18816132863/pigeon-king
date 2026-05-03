# V23.2 Real Work Entry / 真实任务接入版

V23.1 Final AI Shape V2 已经证明“像 AI”。V23.2 的目标是让它开始真正接活：

```text
收到消息
→ RealWorkMessageEntry
→ AIShapeCore / YuanLingSystem
→ GoalContract
→ TaskGraph DAG
→ Constitution Judge
→ WorldInterface
→ ActionLog
→ Checkpoint
→ MemoryWriteback
→ FinalResultReport
```

## 默认入口

- `core.real_work_entry.RealWorkEntry`
- `core.real_work_entry.YuanLingRealWorkEntry`
- `agent_kernel.real_work_entry`
- `yuanling_system.DefaultEntry`

## 执行命令

```bash
tar -xzf pigeon_king_v23_2_real_work_entry_full_replace.tar.gz -C . && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v23_2_apply_real_work_entry.py && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v23_2_verify_real_work_entry.py
```

## 成功标志

```text
PASS: V23.2 Real Work Entry verification passed.
```

## 验收要求

输入一句真实需求，必须生成：

1. GoalContract
2. TaskGraph DAG
3. 风险裁判结果
4. 自动执行任务
5. 等待审批任务
6. checkpoint
7. action log
8. memory writeback
9. 最终结果报告

## 安全边界

- 外部发送、删除、安装、付款等动作默认等待审批。
- 密钥、token、密码外泄直接阻断。
- 默认不会执行未经批准的真实外部副作用。
