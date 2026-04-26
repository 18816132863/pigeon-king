# V10.0.0 Self-Evolving Personal Operating Agent - Clean Full

## AI 形态定义

本版本目标不是“技能集合型 AI”，而是：

**Self-Evolving Personal Operating Agent**
**自进化个人操作系统级自治智能体**

它的核心形态：

一句话目标
→ 自主目标建模
→ 判断是否值得做/能不能做/怎么做更稳
→ 生成任务图
→ 匹配现有能力
→ 能力不足时自动搜索解决方案
→ 形成能力扩展计划
→ 安全审计、沙箱测试、回滚策略
→ 低风险自动执行，高风险强确认
→ 执行结果写入学习闭环
→ 越用越贴近用户本人

## 本版已落地的六个内核

1. 自主决策内核
   - goal_strategy_kernel
   - task_graph_compiler
   - personal_autonomous_os_agent

2. 个人判断与规则内核
   - personal_codex
   - judgement_engine

3. 个性化进化内核
   - personalization_engine

4. 外部能力总线
   - external_capability_bus

5. 自主问题求解内核
   - solution_search_orchestrator

6. 能力自扩展内核
   - capability_self_extension

## 自主边界

这不是无边界乱执行：

- 高风险动作必须强确认
- 未知代码不能直接安装为 active
- 新能力必须先进入 planned / sandbox / experimental
- 必须具备 audit / rollback / minimal test
- 外部 API / 设备权限必须用户授权
- 对矛盾、低质量、违法、高风险目标必须拒绝或要求澄清

## V10 与 V9.2 的区别

V9.2 解决的是：
- 连接端 adapter bootstrap
- L0/L1 小流量安全探测
- adapter_loaded=false 时自动恢复

V10 解决的是：
- 它到底要成为什么 AI
- 如何自主决策
- 如何越用越像用户
- 如何没能力时自己找方案、接能力
- 如何从“执行器”升级为“个人操作系统级自治体”

## 仍需真实环境完成的内容

以下不是压缩包离线能直接完成的，需要运行后授权和学习：

- 真实设备权限授权
- 真实 API key / MCP server / 外部账号接入
- 真实长期行为数据学习
- 真实技能安装源白名单
- 真实联网搜索工具绑定
- 真实高风险动作强确认流程

## 建议冻结名称

Pigeon King / 小艺 Claw V10.0.0
Self-Evolving Personal Operating Agent Clean Full
