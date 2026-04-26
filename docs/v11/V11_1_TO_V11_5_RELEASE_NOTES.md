# Pigeon King V11.1 → V11.5 推进说明

## V11.1 Runtime State Store
新增 `platform_adapter/runtime_state_store.py`：动作先注册再执行，副作用动作生成稳定幂等键，支持队列落表、状态流转、事件审计。

## V11.2 Timeout Budget + Circuit Breaker
新增 `platform_adapter/timeout_circuit.py`：副作用动作遇到 timeout / uncertain 不静默重试，只读动作允许预算内指数退避，连续失败打开熔断器。

## V11.3 Capability Registry
新增 `platform_adapter/capability_registry.py`：不再默认认为设备端已连接，每个能力单独记录 `connected / probe_only / offline / unknown`。

## V11.4 Execution Autopilot
新增 `governance/policy/execution_autopilot.py`：自动组合强确认、能力状态、熔断器、运行台账，输出 `allowed / requires_confirmation / queued / hold_for_result_check`。

## V11.5 Release Gate + Health Report
新增 `infrastructure/ops_health.py` 与 `scripts/v11_5_release_gate.py`：生成 `V11_5_HEALTH_REPORT.json`，汇总队列、动作状态、设备能力、熔断器。

## 一次性验收命令
```bash
/usr/bin/python3 scripts/v11_all_smoke.py
```
