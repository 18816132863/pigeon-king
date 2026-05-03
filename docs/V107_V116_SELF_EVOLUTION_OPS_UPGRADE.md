# V107-V116 自进化生产闭环十连升级

这组版本接在 V97-V106 操作系统级治理层之后，补齐“生产级自进化闭环”。

| 版本 | 大功能 | 模块 |
|---|---|---|
| V107 | Intent Contract 目标契约编译器 | `core/self_evolution_ops/intent_contract.py` |
| V108 | Context Fusion 上下文融合与防膨胀 | `core/self_evolution_ops/context_fusion.py` |
| V109 | Tool Reliability 工具可靠性与熔断 | `core/self_evolution_ops/tool_reliability.py` |
| V110 | Budget Governor token/成本/时间预算治理 | `core/self_evolution_ops/budget_governor.py` |
| V111 | Privacy Redactor 隐私扫描与脱敏 | `core/self_evolution_ops/privacy_redactor.py` |
| V112 | Local Fallback 离线/本地降级方案 | `core/self_evolution_ops/local_fallback.py` |
| V113 | Simulation Lab 执行前仿真评测 | `core/self_evolution_ops/simulation_lab.py` |
| V114 | Preference Drift 偏好漂移监控 | `core/self_evolution_ops/preference_drift.py` |
| V115 | Observability Report 可观测运行报告 | `core/self_evolution_ops/observability_report.py` |
| V116 | Self-Improvement Loop 自改进闭环 | `core/self_evolution_ops/self_improvement_loop.py` |

执行命令：

```bash
unzip -o pigeon_king_v107_v116_self_evolution_ops_upgrade.zip -d . && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v107_v116_apply_self_evolution_ops_upgrade.py && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v107_v116_verify_self_evolution_ops_upgrade.py
```

成功标志：

```text
PASS: V107-V116 self-evolution ops upgrade verification passed.
```

核心边界：

- SECRET 级信息必须脱敏或拒绝。
- 预算超限必须降级或阻断。
- 工具多次失败必须熔断并走 fallback。
- 执行前必须能做 simulation。
- 偏好变化不能直接污染长期记忆。
- 改进建议必须带 rollback plan。
