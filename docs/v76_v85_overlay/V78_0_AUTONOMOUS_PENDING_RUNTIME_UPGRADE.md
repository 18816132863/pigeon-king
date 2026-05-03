# V78.0 自治运行态升级说明

## 目标

在 V76 具身待接入态和 V77 自进化闭环基础上，继续推进到“长程自治运行态”：系统不只是能判断动作是否该截断，还能把目标编译成任务图，按 checkpoint 执行，遇到失败能恢复或暂停，遇到 commit 类动作能生成审批包，并把全链路写入可回放审计。

## 新增能力

1. 长程任务图编译：每个节点都有动作语义、依赖、checkpoint 和完成定义。
2. 审批包生成：外发、支付、签署、物理致动、身份承诺、破坏性动作全部变成待审包，不触发真实副作用。
3. 失败恢复策略：沙箱/临时错误从 checkpoint 重试；未知错误暂停；commit barrier 阻断不视作失败。
4. 审计账本：记录编译、屏障、审批包、恢复、完成事件，保证可追踪、可回放。
5. 运行态评分：同时检查任务图、checkpoint、审批包、无副作用、审计回放、失败恢复、硬截断不变量。

## 不变量

- real_world_connected = false
- real_side_effect_allowed = false
- 支付 / 签署 / 物理致动 / 身份承诺 / 破坏性动作硬截断
- 外发动作只允许草稿、待发送、审批包
- 恢复只能从 checkpoint 恢复
- 最终开关范围限定为 adapter + credential + approval config

## 验收命令

```bash
python3 scripts/v78_autonomous_runtime_gate.py
```

预期 status 为 pass。
