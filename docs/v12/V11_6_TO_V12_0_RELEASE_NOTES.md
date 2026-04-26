# V11.6 → V12.0 连续推进说明

本轮是在 V11.1—V11.5 稳态执行层之后继续推进 5 个版本，目标是把“能跑”推进到“能恢复、能排队、能核验、能验收、能发布”。

## V11.6 Recovery Manager

新增 `platform_adapter/recovery_manager.py`。

能力：
- 扫描 `running / planned / queued / hold_for_result_check` 等非终态动作。
- 对 stale running 动作转回 `queued`，避免进程中断后卡死。
- 对 stale planned 动作转入 `queued`，避免计划态长期悬挂。
- 记录 `runtime_recovery_events`，方便复盘恢复行为。

验收：
```bash
/usr/bin/python3 scripts/v11_6_recovery_smoke.py
```

## V11.7 Delivery Outbox

新增 `platform_adapter/delivery_outbox.py`。

能力：
- 对 `runtime_delivery_queue` 提供本地 lease。
- 执行器只消费 leased item，不直接跳过队列。
- 成功后生成 outbox receipt 并转 `completed`。
- 副作用动作 timeout / uncertain 时转 `hold_for_result_check`，禁止静默重试，防止重复发短信、重复建日程、重复通知。

验收：
```bash
/usr/bin/python3 scripts/v11_7_outbox_smoke.py
```

## V11.8 Result Verifier

新增 `platform_adapter/result_verifier.py`。

能力：
- 为动作生成结果契约。
- 校验 `ok / status / receipt` 等必填字段。
- 结果不完整或 timeout / unknown / partial 时不直接完成，转 `hold_for_result_check`。
- 结果满足契约后才转 `completed`。

验收：
```bash
/usr/bin/python3 scripts/v11_8_result_verifier_smoke.py
```

## V11.9 Acceptance Matrix

新增 `infrastructure/acceptance_matrix.py`。

覆盖场景：
1. 低风险直连允许。
2. 高风险副作用动作需要确认或排队。
3. 副作用 timeout 禁止静默重试。
4. 结果契约满足后完成。
5. stale running 动作可恢复。

验收：
```bash
/usr/bin/python3 scripts/v11_9_acceptance_matrix_smoke.py
```

## V12.0 Release Manifest

新增 `infrastructure/release_manifest.py`。

能力：
- 生成文件 manifest。
- 执行 acceptance matrix。
- 汇总 ops health。
- 输出 `V12_0_RELEASE_MANIFEST.json`。
- 作为最终发布门禁。

验收：
```bash
/usr/bin/python3 scripts/v12_0_final_gate.py
```

## 总验收

```bash
/usr/bin/python3 scripts/v11_6_to_v12_0_all_smoke.py
```

注意：统一使用 `/usr/bin/python3`，不要用环境里异常的 `/opt/pyvenv/bin/python`。
