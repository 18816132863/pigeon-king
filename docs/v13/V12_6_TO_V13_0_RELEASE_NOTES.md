# V12.6 → V13.0 推进说明

本轮继续在 V12.5 基线后推进 5 个版本，目标是把系统从“可验收”推进到“可长期运行、可审计、可生产门禁”。

| 版本 | 模块 | 目标 |
|---|---|---|
| V12.6 | `platform_adapter/self_healing_supervisor.py` | 自愈监督器：自动恢复 stale running 和过期 leased 队列 |
| V12.7 | `governance/audit/execution_audit_ledger.py` | 执行审计台账：记录谁、什么动作、为什么允许/阻断 |
| V12.8 | `governance/policy/risk_tier_matrix.py` | 风险分级矩阵：L1-L4 分级，副作用动作强确认，破坏性动作阻断 |
| V12.9 | `infrastructure/long_run_soak.py` | 长期运行压测：重复执行、幂等探测、SLO、审计、风险摘要 |
| V13.0 | `infrastructure/production_gate.py` | 生产门禁：汇总自愈、审计、风险、SLO、压测、升级门禁和发布清单 |

## 总验收命令

```bash
/usr/bin/python3 scripts/v12_6_to_v13_0_all_smoke.py
```

## 单项验收命令

```bash
/usr/bin/python3 scripts/v12_6_self_healing_smoke.py
/usr/bin/python3 scripts/v12_7_audit_ledger_smoke.py
/usr/bin/python3 scripts/v12_8_risk_matrix_smoke.py
/usr/bin/python3 scripts/v12_9_long_run_soak_smoke.py
/usr/bin/python3 scripts/v13_0_production_gate.py
```

## 关键原则

- 不依赖外部服务；所有烟测使用本地 SQLite 临时库。
- 不绕过强确认；高风险动作默认进入 `requires_confirmation`。
- 不让队列永久卡死；过期 leased 会被自愈监督器恢复为 pending。
- 不只看是否能跑通；V13.0 生产门禁会聚合审计、SLO、压测、升级和发布清单。
