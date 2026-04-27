# V36.0 → V45.0 大版本推进说明

本轮继续向“自进化个人自治操作代理”推进，保持六层架构，不新增 L7。

| 版本 | 大功能 | 架构归属 |
|---|---|---|
| V36.0 | Mission Outcome Contract：一句话目标转可验收目标契约 | L1/L3 |
| V37.0 | Handoff Bus：专家代理交接、职责边界、trace | L3 |
| V38.0 | Personal Pattern Learner：情节/程序偏好学习请求 | L2 |
| V39.0 | Tool Guardrail Runtime：每次工具调用前后 guardrail | L5 |
| V40.0 | Device Transaction Saga：端侧动作事务化、串行、幂等、回执 | L4 |
| V41.0 | Capability Gap Autodiscovery：能力缺口、候选、沙箱扩展决策 | L3/L5/L6 |
| V42.0 | Scenario Simulator：执行前情景仿真和阻断预测 | L3/L6 |
| V43.0 | Autonomy Budget Scheduler：自治预算与长任务边界 | L5/L6 |
| V44.0 | Continuous Improvement Evaluator：运行后评估与受控学习建议 | L2/L5 |
| V45.0 | Autonomous OS Supreme Gate：总门禁 | L5/L6 |

强规则：agent_kernel 仍归 L3；所有端侧多动作必须串行；超时先 pending_verify，不误判离线；记忆写入必须走 Memory Guard；能力扩展必须沙箱、评估、回滚。

验收命令：

```bash
/usr/bin/python3 scripts/v23_1_to_v45_0_full_replace_gate.py
/usr/bin/python3 scripts/v36_0_to_v45_0_all_smoke.py
/usr/bin/python3 scripts/v45_0_autonomous_os_supreme_gate.py
```
