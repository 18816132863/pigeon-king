# V23.2 → V23.6 Release Notes

本包是在 V23.1 基础上的继续推进包，不是 clean merge 包。

## V23.2 Six-Layer Architecture Boundary Guard
- 固定六层主架构。
- agent_kernel / 自治器官归属 L3 Orchestration。
- 禁止 L7 / 第七层表述进入架构定义。

## V23.3 Agent Hub Boundary Contract
- agent_kernel 只做总编排。
- 风险判断必须交给 L5 Governance。
- 工具执行必须交给 L4 Execution。
- 长期记忆必须交给 L2 Memory Context。
- 中断恢复必须交给 L6 Infrastructure。

## V23.4 Device Action Timeout Verification
- 端侧已连接时，动作超时不等于设备离线。
- modify_alarm 超时后先二次 search 验证。
- search_alarm 默认从 rangeType=all 降级为 next。
- 闹钟 + 负一屏 + 主对话框推送强制串行顺序。

## V23.5 Compact Resume Policy
- 长任务上下文压缩后，从 task_state/pending_steps 恢复。
- 不重复执行 completed_steps。
- 不依赖聊天上下文猜测恢复点。

## V23.6 Organ Conflict Policy
- “器官”定义为能力组，不是架构层。
- 统一器官归属，避免中枢之间互相抢权。

## 验收命令

```bash
/usr/bin/python3 scripts/v23_2_to_v23_6_all_smoke.py
```
