# SKILL_ACCESS_RULES.md - 主动技能联想规则

## 目标

技能不能只靠用户说出关键词才触发。系统应根据用户的场景、任务、文件类型、风险、上下文主动推荐候选技能。

## 分层

1. `trigger_keywords`：被动触发词。用户明确说出时优先匹配。
2. `context_triggers`：主动场景触发。用户描述场景但没说技能名时，用它联想。
3. `proactive_scenario`：自然语言说明“什么时候应该主动推荐”。
4. `skill_policy_gate`：判断该技能是否 offline_safe / mock_only / approval_required / external_api_blocked。
5. `V90/V92/V100 commit barrier`：决定能否执行。主动推荐永远不能绕过它。

## 行为规则

- 只推荐，不自动执行。
- 每次最多推荐 3-5 个候选技能，避免打扰。
- 如果用户需求明确、当前能力明显匹配，可以主动说“这个场景适合用 X 技能”。
- 如果技能需要外部 API，而 `NO_EXTERNAL_API=true`，只能推荐 mock/dry-run 或说明被禁用。
- 如果涉及支付、签署、外发、设备、删除、身份承诺，必须标记 `approval_required`，不得自动执行。
- 用户说“不用推荐技能”后，本轮应降低推荐频率。

## 推荐话术

优先简短：

> 这个场景适合调用：A / B / C。我先按离线 dry-run 方式准备，不做真实外发。

不要每次都长篇解释。
