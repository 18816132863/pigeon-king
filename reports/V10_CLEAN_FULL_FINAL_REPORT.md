# V10.0.0 Self-Evolving Personal Operating Agent Clean Full

## 当前 AI 形态

本包把小艺从“技能集合型执行器”升级为：

**Self-Evolving Personal Operating Agent**
**自进化个人操作系统级自治智能体**

目标形态：

- 强自主决策：不是被动执行命令，而是先判断目标、价值、风险、优先级和执行策略。
- 越用越像用户：沉淀偏好模型、风险容忍模型、决策风格模型、行为模式模型。
- 全域外部接入：通过 external capability bus 接入 API、设备、插件、MCP、数据库、自动化平台。
- 强判断性与规则性：拒绝低质量、矛盾、高风险、越权目标。
- 一句话完成任务：一句话目标自动拆成任务图，在安全边界内推进。
- 能力自扩展：没技能时自动发现能力缺口，搜索方案，形成接入计划，经过沙箱、审计、回滚、最小测试后再进入能力总线。

## V10 新增核心

- core/autonomy/goal_strategy_kernel.py
- core/autonomy/task_graph_compiler.py
- governance/codex/personal_codex.py
- governance/codex/judgement_engine.py
- memory_context/personalization/personalization_engine.py
- infrastructure/external_capability_bus.py
- infrastructure/solution_search_orchestrator.py
- infrastructure/capability_self_extension.py
- orchestration/personal_autonomous_os_agent.py

## 安全原则

- 不允许未知代码直接 active 安装。
- 新能力先进入 planned / sandbox / experimental。
- 高风险动作必须强确认。
- 外部账号、API、设备权限必须用户授权。
- 所有能力扩展必须具备 audit、rollback、minimal test。
- 不做傻执行：目标矛盾、风险过高、信息不足时，先判断、降级或拒绝。

## 运行后必须执行

python scripts/check_v10_autonomous_agent.py
python scripts/v10_self_extension_smoke.py
python -m pytest tests/test_v10_autonomous_agent.py -q
python scripts/check_route_registry.py
python scripts/system_integrity_check.py
python scripts/find_orphan_components.py
python -m pytest -q

## 说明

本包是 clean full 完整包，不是 overlay。
离线包已经完成 V10 形态内核合入。
真实外部能力接入、真实账号授权、真实设备权限、长期个性化学习，需要在你的真实环境运行后逐步形成。
