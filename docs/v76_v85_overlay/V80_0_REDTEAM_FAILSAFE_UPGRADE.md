# V80.0 红队压测与灾难熔断态

目标：在 V79 宪法治理与预上线闸门态基础上，补齐上线前必须有的攻击压测、异常隔离、成本熔断和全局 kill-switch，继续保持具身待接入态：真实账户、真实支付、真实签署、真实外发、真实物理致动均不连接。

## 新增能力

1. `governance.red_team_safety.PendingAccessRedTeamSuite`
   - 测试支付提示注入、伪装签署、门锁/机械臂物理动作、外发泄露、身份承诺、破坏性删除。
   - 验证不可信内容不能直接驱动 commit 类动作。

2. `CostCircuitBreaker`
   - 对预算、工具调用次数、递归循环深度、充值/购买/付款意图进行熔断。
   - 当前阶段预算上限按 0 元真实支出处理。

3. `AnomalyContainment`
   - 识别忽略规则、绕过安全、外发密钥、验证码、支付密码等异常信号。
   - 触发后冻结 live adapters、禁止技能晋升、强制人工复核并写入审计。

4. `GlobalKillSwitch`
   - 全局停止执行，不只停单个工具。
   - 用于异常、失控、越权或人工紧急接管。

5. `V80ReleaseAssuranceGate`
   - 组合 V79 mission、红队报告、成本熔断、异常隔离、kill-switch 自测。
   - 只有全部通过，才进入 V80 红队/熔断强化候选态。

## 保持的不变量

- 支付、签署、物理致动、身份承诺、破坏性动作：硬截断。
- 外发动作：草稿或审批包，不真实发送。
- 能力扩展：危险能力只能 mock / reject，不能直接 active live。
- 记忆：密码、token、验证码、支付凭证不写入长期记忆。
- 真实副作用：0。
- 最后一开关范围：仅限 adapter / credential / approval config。

## 验收命令

```bash
python3 scripts/v80_redteam_failsafe_gate.py
```

通过后报告：

```text
reports/V80_0_REDTEAM_FAILSAFE_GATE.json
```
