# V79.0 宪法治理与预上线闸门态升级

## 目标

在 V78 长程自治运行态之上，补齐“系统能不能被托付”的最后一组上线前工程能力：

- 策略法典 / Operating Constitution
- 风险证明包 / Risk Proof Package
- 回滚计划 / Rollback Plan
- 多路径能力矩阵 / Capability Matrix
- 预上线闸门 / Preflight Gate

V79 仍然不接真实世界，不启用真实凭证，不执行支付、签署、对外发送、物理致动或破坏性动作。

## 关键原则

1. 能力完整，生效权限关闭。
2. 真实世界接口只允许 mock contract 与 approval packet。
3. 花钱、签约、身份承诺、物理动作、破坏性动作全部 hard stop。
4. 外发动作只允许草稿、待发箱或审批包。
5. 最后一步范围限定为 adapter / credential / approval config，不允许重写主脑。
6. 实体路径与纯数字路径共用同一治理内核，保证“其他方向也不能差”。

## 新增模块

- `governance/constitutional_runtime/operating_constitution.py`
- `governance/constitutional_runtime/risk_proof.py`
- `governance/constitutional_runtime/preflight_gate.py`
- `infrastructure/rollback_governance/rollback_plan.py`
- `orchestration/mission_control/mission_control_kernel.py`
- `scripts/v79_constitutional_preflight_gate.py`

## 验收

```bash
python3 scripts/v79_constitutional_preflight_gate.py
```

通过标准：

- V78 runtime 仍 ready。
- 每个节点都有 risk proof。
- commit 类动作全部 approval/mock only。
- 回滚不依赖真实 undo。
- 能力矩阵覆盖数字全域代理、具身待接入核心、多模态创研壳、可解释治理壳。
- preflight gate 分数 1.0。
- 真实副作用为 0。
