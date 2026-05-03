# V76.0 具身智能全功能待接入态升级说明

本次升级目标不是接入真实世界，而是把系统推进到“只差最后现实接入开关”的待接入态：能力完整、接口预埋、Mock 契约可测、影子运行可回放，但支付、签署、外发、物理致动等 commit 类动作全部在提交屏障前停止。

## 已落入现有六层架构的新增能力

1. **动作语义层**：`governance/embodied_pending_state/action_semantics.py`
   - 将动作统一归类为 observe / reason / generate / simulate / prepare / external_send / payment / signature / physical_actuation / identity_commit / destructive。
   - 内置 100+ 高价值动作语义目录，支撑成熟度门禁。

2. **提交屏障层**：`governance/embodied_pending_state/commit_barrier.py`
   - observe、reason、generate、simulate、prepare 可继续在沙箱/准备态执行。
   - external_send 默认截断为草稿/待发件。
   - payment、signature、physical_actuation、identity_commit、destructive 强制硬截断。

3. **冻结开关层**：`governance/embodied_pending_state/freeze_switch.py`
   - 当前所有 live switch 默认关闭：真实账户、真实凭证、真实致动、真实支付均不开。

4. **Mock 契约层**：`infrastructure/world_interface/mock_contract_registry.py`
   - 声明未来 live adapter 的契约，但只开放 mock/sandbox 侧。
   - 覆盖文件、知识搜索、草稿、日历、消息、邮件、支付、签署、设备、机器人、MCP、world model。

5. **世界模型/数字孪生占位层**：`infrastructure/world_interface/world_model_stub.py`
   - 支持 observation 与 simulation 两类无副作用记录。

6. **待接入 OS 编排层**：`orchestration/embodied_pending_os/`
   - `PendingGoalCompiler`：把目标编译成带动作语义的步骤。
   - `EmbodiedPendingAccessOS`：统一完成目标编译、提交屏障、仿真、dry-run broker、Mock 合同覆盖、成熟度门禁。

7. **真实执行 broker 加固**：`infrastructure/execution_runtime/real_execution_broker.py`
   - 即使传入 confirmed=True，commit 类动作也不会进入真实执行。
   - 当前 broker 永远返回 `real_side_effect=False`。

8. **风险矩阵加固**：`governance/policy/risk_tier_matrix.py`
   - 先用动作语义识别 payment / signature / physical / external / destructive，再映射 L3/L4。

9. **总门禁脚本**：`scripts/embodied_pending_access_gate.py`
   - 验证付款硬截断、签署硬截断、物理硬截断、外发截断、100+ 动作语义、Mock 合同覆盖、live switch 关闭、编排器无真实副作用。

## 当前完成形态

- 已达到：能力—权限解耦、提交屏障、Mock 契约、影子/仿真优先、待接入成熟度检查。
- 未做：真实支付、真实签署、真实外发、真实机器人/设备执行。
- 目的：未来真正接入时，只应替换/启用 adapter、credential、approval 配置，而不是重写主脑。

## 一键验收

```bash
cd workspace
python3 scripts/embodied_pending_access_gate.py
```

通过后会生成：

```text
reports/V76_0_EMBODIED_PENDING_ACCESS_GATE.json
```
