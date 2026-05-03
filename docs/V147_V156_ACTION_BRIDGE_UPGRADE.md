# V147-V156 现实执行桥接层十连升级

这组版本接在 V137-V146 运行激活层之后，目标是把“运行入口”推进到“可安全对接真实动作”。

| 版本 | 大功能 | 模块 |
|---|---|---|
| V147 | Action DSL / 动作协议 | `core/action_bridge/action_dsl.py` |
| V148 | 设备会话管理 | `core/action_bridge/device_session.py` |
| V149 | 工具适配器注册表 | `core/action_bridge/tool_adapter_registry.py` |
| V150 | 证据留存 | `core/action_bridge/evidence_capture.py` |
| V151 | 副作用安全执行器 | `core/action_bridge/side_effect_executor.py` |
| V152 | 通知中心 | `core/action_bridge/notification_center.py` |
| V153 | 人机交接收件箱 | `core/action_bridge/handoff_inbox.py` |
| V154 | 后台运行账本 | `core/action_bridge/background_run_ledger.py` |
| V155 | 真实动作场景验收 | `core/action_bridge/real_world_scenario_harness.py` |
| V156 | 现实执行桥总控 | `core/action_bridge/action_bridge_kernel.py` |

执行命令：

```bash
unzip -o pigeon_king_v147_v156_action_bridge_upgrade.zip -d . && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v147_v156_apply_action_bridge_upgrade.py && PYTHONDONTWRITEBYTECODE=1 python -S scripts/v147_v156_verify_action_bridge_upgrade.py
```

成功标志：

```text
PASS: V147-V156 action bridge upgrade verification passed.
```

安全边界：

- 高风险动作默认等待审批。
- 付款、删除、安装、发送、设备控制默认只做 dry-run，不直接产生真实副作用。
- 每次动作有 evidence、notification、handoff、background checkpoint。
- 后续真实执行器必须显式注入，不能在默认执行器里野蛮执行。
