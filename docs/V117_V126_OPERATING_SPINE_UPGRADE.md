# V117-V126 统一操作脊柱十连升级

这组版本接在 V107-V116 后面，目标是把前面所有能力从“模块集合”串成“统一运行脊柱”。

| 版本 | 大功能 | 模块 |
|---|---|---|
| V117 | 统一事件总线 | `core/operating_spine/event_bus.py` |
| V118 | 状态迁移管理器 | `core/operating_spine/state_migration.py` |
| V119 | 能力契约注册表 | `core/operating_spine/capability_contracts.py` |
| V120 | 任务运行时适配器 | `core/operating_spine/task_runtime_adapter.py` |
| V121 | 审批恢复工作流 | `core/operating_spine/approval_recovery.py` |
| V122 | 连接器健康监控 | `core/operating_spine/connector_health.py` |
| V123 | 记忆压缩整合器 | `core/operating_spine/memory_consolidation.py` |
| V124 | 技能生命周期管理器 | `core/operating_spine/skill_lifecycle.py` |
| V125 | 端到端场景测试器 | `core/operating_spine/scenario_harness.py` |
| V126 | 统一操作脊柱内核 | `core/operating_spine/operating_spine.py` |

执行命令：

```bash
unzip -o pigeon_king_v117_v126_operating_spine_upgrade.zip -d . && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v117_v126_apply_operating_spine_upgrade.py && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v117_v126_verify_operating_spine_upgrade.py
```

成功标志：

```text
PASS: V117-V126 operating spine upgrade verification passed.
```

这组版本解决的问题：

- 前面 V85-V116 不再是散模块，而是有统一事件、统一状态、统一契约、统一运行时。
- 高风险动作可等待审批并从 checkpoint 恢复。
- 连接器有健康监控和降级策略。
- 记忆可压缩，技能可 canary 和 rollback。
- 每次升级有端到端场景验收。
