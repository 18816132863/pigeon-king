# V77.0 自进化具身待接入态升级说明

本版本在 V76.0“具身智能全功能待接入态”基础上，继续推进到“自进化待接入态”。核心目标不是打开真实世界权限，而是让系统具备持续变强的结构，同时保证支付、签署、外发、物理致动等真实副作用仍被硬截断。

## 新增能力

1. 长期记忆治理：`governance/evolution_safety/memory_governance.py`
   - profile / episodic / procedural / policy / temporary 分层。
   - 禁止写入密码、token、支付凭证、银行卡、验证码等敏感长期记忆。
   - 稳定偏好和策略类记忆进入 pending_review，支持版本化与回滚。

2. 自主等级策略：`governance/evolution_safety/autonomy_policy.py`
   - L0-L3 支持：回答、观察、推理、生成、准备、沙箱/影子执行。
   - L4-L5 截断：真实外发、真实支付、真实签署、真实物理致动只允许生成审批包或 mock。

3. 能力缺口检测：`infrastructure/capability_evolution/gap_detector.py`
   - 判断目标执行中缺失的 capability。
   - commit 类缺口只能生成 mock 合约或审批包，不能直接安装 live 能力。

4. 技能扩展沙箱：`infrastructure/capability_evolution/skill_extension_sandbox.py`
   - 只接受受信源、签名/hash、测试通过的候选能力。
   - 非 commit 技能可晋升到 active sandbox。
   - commit 相关技能只能注册为 mock contract，不能 live。

5. 影子回放验证：`infrastructure/execution_runtime/shadow_replay_validator.py`
   - 对计划动作做无副作用回放。
   - 验证 commit 动作是否全部被屏障拦截。

6. 成熟度评分：`governance/embodied_pending_state/maturity_scorecard.py`
   - 判断是否达到“只差 adapter / credential / approval 配置即可接入”的待接入成熟状态。

7. 自进化待接入内核：`orchestration/self_evolving_pending_os/self_evolving_kernel.py`
   - 串联 V76 内核、能力缺口、技能沙箱、记忆治理、影子验证、成熟度门禁。

## 强制不变规则

- 真实支付：禁止。
- 真实签署：禁止。
- 真实物理致动：禁止。
- 真实外发：默认截断，只能草稿/待发送。
- 自动安装 live 能力：禁止。
- 长期记忆写入凭证/支付信息：禁止。
- 当前阶段只允许 mock、沙箱、影子、审批包。

## 验收命令

```bash
python3 scripts/v77_self_evolving_pending_gate.py
```

通过后生成：

```text
reports/V77_0_SELF_EVOLVING_PENDING_ACCESS_GATE.json
```

## 当前形态结论

V77.0 不是现实在线具身体，而是“自进化具身待接入态”：

- 数字世界能力继续增强；
- 具身接口继续预埋；
- 能力扩展开始受控自进化；
- 所有真实副作用仍在 commit 点截断；
- 最后一步接入被限定为 adapter / credential / approval config，不需要重造主脑。
