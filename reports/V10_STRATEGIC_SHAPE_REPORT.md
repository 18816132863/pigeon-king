# V10 战略形态：自进化个人自治操作代理

版本：V10.0.0
基底：V9.2.0 Connected Adapter Bootstrap
目标形态：Self-Evolving Personal Operating Agent

## 形态定义

V10 不再定位为“更多技能集合”或“更会执行命令的小艺”，而是升级为你的第二操作系统：

- 能把一句话目标编译成目标树、约束集、执行图和验收标准。
- 能根据你的偏好、风险容忍度、表达方式和做事习惯调整策略。
- 能先判断、再执行，低风险自动推进，高风险强确认。
- 能接入外部 API / MCP / connector / 设备 / 数据库作为能力候选。
- 能发现能力缺口，自动搜索方案，形成沙箱化能力扩展计划。
- 能把成功经验写回程序性记忆，使后续越来越像你。

## 新增长出来的 6 个能力器官

1. 目标—策略内核：core/autonomy/goal_strategy_kernel.py
2. 任务图编译器：core/autonomy/task_graph_compiler.py
3. 个人法典与裁判层：governance/codex/
4. 个性化记忆内核：memory_context/personalization/
5. 外部能力总线：infrastructure/external_capability_bus.py
6. 能力自扩展内核：infrastructure/capability_self_extension.py

## 重要安全边界

V10 支持“自动找方案、自动形成能力接入计划”，但不允许无审计地直接安装和执行未知代码。

所有能力扩展必须满足：

- no_untrusted_direct_install = true
- sandbox_required = true
- rollback_required = true
- approval_required_for_executable_code = true
- promote_only_after_minimal_tests = true

## 一句话任务流程

用户一句话目标 → 目标建模 → 个人法典裁判 → 能力解析 → 执行图生成 → 缺能力则搜索方案 → 沙箱评估 → 安全执行 → 验收 → 写回学习闭环。

## 当前交付性质

这是 V10 形态内核版，重点是让系统具备“自主决策 + 个性化 + 能力自扩展”的稳定骨架。
真实外部联网搜索、真实技能安装、真实 MCP marketplace 接入应在下一阶段接入，但必须继续走本版的法典、沙箱、审批和回滚链路。
