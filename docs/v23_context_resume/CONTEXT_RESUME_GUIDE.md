# Context Resume 防卡死机制

目的：把长任务的关键状态写到 `task_state/current_task_state.json`，避免聊天上下文压缩、模型重启、UI 中断后无法继续。

## 核心文件

- `infrastructure/context_resume.py`
- `scripts/resume_current_task.py`
- `scripts/context_resume_smoke.py`
- `task_state/current_task_state.json`（运行时生成）
- `task_state/context_resume_events.jsonl`（运行时生成）

## 固定恢复命令

```bash
/usr/bin/python3 scripts/resume_current_task.py
```

输出会包含：

- 当前 task_id
- 当前版本
- 当前阶段
- 已完成步骤
- 待完成步骤
- 上一次输出文件
- 下一条命令
- 恢复指令

## 验收命令

```bash
/usr/bin/python3 scripts/context_resume_smoke.py
```

## 强制规则

长任务入口必须优先写状态文件；阶段完成后必须更新状态文件；上下文压缩后不得重新分析全部聊天历史，必须读取 `task_state/current_task_state.json` 后从 `pending_steps` 继续。
