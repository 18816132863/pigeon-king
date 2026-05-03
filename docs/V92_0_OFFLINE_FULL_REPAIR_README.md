# V92.0 离线全量接管修复包

用途：
- 修复 4 个核心空架子：知识图谱、偏好演化、自我改进、记忆写回守卫。
- 将已写未集成模块登记到 offline/mock/dry-run 集成注册表。
- 将外部基础设施统一降级为本地替身/Mock Contract。
- 修复 solution_search 在离线模式下的 gateway_error。
- 不调用外部 API，不真实支付、签署、外发或物理执行。

执行：
```bash
cd ~/openclaw
unzip workspace_V92_0_offline_full_repair_overlay.zip
cd workspace
python3 -S scripts/v92_full_static_audit_and_repair_gate.py
```

报告：
- `reports/V92_APPLY_OFFLINE_REPAIR.json`
- `reports/V92_FULL_STATIC_AUDIT_AND_REPAIR_GATE.json`
