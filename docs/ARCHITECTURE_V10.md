# 🏗️ 鸽子王 V10.0 架构总览

Self-Evolving Personal OS Agent

> 更新时间: 2026-05-03 · 架构版本: V10.1.0

---

## 📐 架构全景

鸽子王采用 **六层架构**，从底层基础设施到顶层核心认知，每层各有明确的职责边界。

```
┌─────────────────────────────────────────────────────────────────────┐
│  L1  Core          核心认知 · 身份 · 规则 · 标准 · 监控            │
├─────────────────────────────────────────────────────────────────────┤
│  L2  Memory        记忆上下文 · 知识库 · 多模态搜索 · 学习循环     │
├─────────────────────────────────────────────────────────────────────┤
│  L3  Orchestration 任务编排 · 工作流 · 规划 · 路由 · 模型管理      │
├─────────────────────────────────────────────────────────────────────┤
│  L4  Execution     能力执行 · 工具绑定 · 推测解码 · 视觉操作       │
├─────────────────────────────────────────────────────────────────────┤
│  L5  Governance    安全治理 · 访问控制 · 宪法裁判 · 审计 · 策略    │
├─────────────────────────────────────────────────────────────────────┤
│  L6  Infrastructure 基础设施 · 工具链 · 平台适配 · 存储 · 网络    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📂 目录结构

### L1 Core — 核心认知层 (487 .py 文件)

| 目录 | 功能 |
|------|------|
| `core/llm/` | 大模型引擎 — 注册表、路由、决策矩阵、任务画像 |
| `core/executive_os/` | 操作系统内核 — 命令编译、模式切换、闭环引擎 |
| `core/autonomy/` | 自主决策 — 目标策略、任务编译器、连续运行 |
| `core/mission/` | 任务控制 — 任务规划图、优先级引擎、主动观察 |
| `core/authorization/` | 授权门控 — 意图认证、同意管理、风险证明 |
| `core/reality/` | 现实接地 — 事实状态解析、环境探针、不确定性管理 |
| `core/personality/` | 个性管理 — 个性漂移防护 |
| `core/persona/` | 人物角色管理 |
| `core/skill_entry/` | 技能入口 — 输入路由、验证、格式化 |
| `core/skill_asset_registry/` | 技能资产管理 — 注册、扫描、发现 |
| `core/personalization/` | 个性化引擎 |
| `core/world_model/` | 世界模型 — 环境抽象 |
| `core/monitoring/` | 监控 — 健康监控、性能指标 |
| `core/privacy/` | 隐私 — 敏感数据过滤 |
| `core/self_evolution_ops/` | 自演化运维 |
| `core/self_governance/` | 自治理 |
| `core/self_test/` | 自测试 — 完美门控 |
| `core/real_work_entry/` | 工作入口 — 消息入口、存储、动作日志 |
| `core/real_tool_binding/` | 工具绑定 — 绑定器、执行器、内核 |
| `core/project_autonomy/` | 项目自治 |
| ... | (共~45个子模块) |

### L2 Memory Context — 记忆上下文层 (70 .py 文件)

| 目录/文件 | 功能 |
|-----------|------|
| `memory_context/vector/qdrant_store.py` | **Qdrant 向量存储** — 支持5种embedding模式（gitee_api/local_onnx/hash_n_gram/deepseek_api/manual） |
| `memory_context/personal_memory_kernel_v4.py` | 个人记忆内核 V4 — 写回防护 |
| `memory_context/personal_knowledge_graph_v5.py` | 个人知识图谱 V5 |
| `memory_context/preference_evolution_model_v7.py` | 偏好演化模型 V7 |
| `memory_context/memory_writeback_guard_v2.py` | 记忆写回防护 V2 |
| `memory_context/cross_lingual/` | 跨语言搜索 — CrossLingualSearcher |
| `memory_context/multimodal/` | 多模态搜索 — MultimodalSearcher |
| `memory_context/vector/` | 向量嵌入引擎 + 缓存管理 |
| `memory_context/learning_loop/` | **学习循环** — 审计回放、元学习、模式提取、成功路径存储 |
| `memory_context/persona/` | **V102+V103+V103.1: 人格连续性层 + 持续意识流(已降级为隐喻)** — 状态机、关系记忆、情绪标签记忆、反思日志、连续性摘要、语气渲染、一致性校验器、语气稳定器、**持续意识流引擎(降级为simulated_by_context_capsule)**（见下文详细说明） |
| `memory_context/context/` | **V103: 上下文重载层** — 上下文胶囊、会话交接包、记忆启动召回器、优先级路由（见下文详细说明） |

**使用示例：**

```python
from memory_context.vector.qdrant_store import QdrantMemoryStore, QdrantMemoryKernelBridge

# 默认使用 gitee_api 模式（Qwen3-Embedding-8B，1024维）
store = QdrantMemoryStore()
store.add("用户喜欢简洁的回复风格", {"type": "preference", "confidence": 0.95})

# 语义搜索
results = store.search("用户喜欢什么风格")
# → "用户喜欢简洁的回复风格" score=0.7184

# 或通过记忆内核门控（自动拒绝低置信度内容）
bridge = QdrantMemoryKernelBridge()
bridge.write("低置信度的内容", confidence=0.5)  # → rejected
```

**embedding 模式切换：**
- `gitee_api`（默认）：Gitee AI + Qwen3-Embedding-8B，需从 `~/.openclaw/env/gitee_ai.env` 读取 API Key
- `hash_n_gram`：纯本地零依赖，用字符哈希做向量
- `local_onnx`：fastembed 本地推理（需下载模型）
- `manual`：外部提供向量

**存储位置：** `~/.openclaw/memory/qdrant/`

### L3 Orchestration — 编排层 (130 .py 文件)

| 目录 | 功能 |
|------|------|
| `orchestration/router/` | **模型路由** — 智能任务路由 (`core/llm/model_router.py` V85) |
| `orchestration/planner/` | **规划器** — 目标解析、任务分解、路由选择、技能选择 |
| `orchestration/workflows/` | 工作流引擎 — 电商、补偿、人力资源确认等 |
| `orchestration/autonomous_task_runtime/` | 自主任务运行时 — 审批包、失败恢复、任务图 |
| `orchestration/embodied_pending_os/` | 具身待接入 OS — 目标编译、待接入编排器 |
| `orchestration/final_pending_release/` | 最终发布 — V85 最终内核、冻结清单、影子验收 |
| `orchestration/mission_control/` | 任务控制内核 |
| `orchestration/self_evolving_pending_os/` | 自演化待接入 OS |
| `orchestration/task_state/` | 任务状态管理 |
| `orchestration/conversation/` | 对话管理 |
| `orchestration/streaming/` | LLM 流式处理 |
| `orchestration/durable_task_graph_engine_v6.py` | Durable 任务图引擎 |
| `orchestration/device_serial_call.py` | 设备串行调用 |
| `orchestration/runtime_bus.py` | **V104.3: 运行时总线** — 各运行时组件之间的协调消息通道，commit barrier 桥接 |
| `orchestration/single_runtime_entrypoint.py` | **V104.1: 单运行时入口** — 统一运行时调度入口，V104.3 追加 commit barrier / runtime bus 引用 |

### L4 Execution — 执行层 (94 .py 文件)

| 目录 | 功能 |
|------|------|
| `execution/speculative_decoding/` | **推测解码** — Draft-Target 架构解码 |
| `execution/speculative_decoding_v1/` | 推测解码 V1 |
| `execution/visual_operation_agent/` | **视觉操作 Agent** — 屏幕观察、UI 接地、视觉规划 |
| `execution/capabilities/` | **能力注册** — 审批操作、日历检查、联系人管理、文件管理等 |
| `execution/failover/` | 故障转移 |
| `execution/optimizer/` | 自动调优器 |
| `execution/quantization/` | INT8 量化 |
| `execution/rag/` | RAG 优化器 |
| `execution/vector_ops/` | 向量运算 |

### L5 Governance — 安全治理层 (88 .py 文件)

| 目录 | 功能 |
|------|------|
| `governance/policy/` | **策略引擎** — 运行时策略、自治层级策略、端侧全局串行策略、执行自动驾驶、故障分类 |
| `governance/access_control/` | **访问控制** — 权限管理器、权限租约管理 |
| `governance/constitutional_runtime/` | **宪法运行时** — 运行宪法、前置门控、风险证明 |
| `governance/embodied_pending_state/` | **具身待接入状态** — 提交屏障、动作语义、冻结开关、就绪门控、成熟度评分 |
| `governance/evolution_safety/` | **演化安全** — 自治策略、记忆治理、个性记忆审计 |
| `governance/red_team_safety/` | **红队安全** — 断路器、红队套件、发布保证 |
| `governance/safety_governor/` | 安全阀门 — 审批门控、运行时门控 |
| `governance/scheduler/` | 实时调度器 |
| `governance/security/` | 安全确认 |
| `governance/audit/` | 审计 |
| `governance/review/` | 审查 |
| `governance/persona/` | **V102: 类人行为策略** — 16条行为规则（5条红线），人格层不覆盖治理层的铁律（见下文） |
| `governance/context/` | **V103: 防上下文失忆守卫** — 检测 handoff/capsule 可用性，触发时读取不瞎猜（见下文） |
| `governance/runtime_commit_barrier_bridge.py` | **V104.3: 提交屏障桥** — runtime_bus 和 V90 commit barrier 之间的协调桥梁 |
| `governance/fused_modules/` | **融合引擎** — V1~V2 融合模块，包括 `doc_fusion_V10*.json` 等版本注册 |

### L6 Infrastructure — 基础设施层 (323 .py 文件)

| 目录 | 功能 |
|------|------|
| `infrastructure/platform_adapter/` | **平台适配器** — 小艺通道适配、调用账本、结果归一化、自修复、超时断路器、快照管理 |
| `infrastructure/device_capability_bus/` | **设备能力总线** — 执行器、注册表、模式 |
| `infrastructure/world_interface/` | **世界接口** — 通用世界解析器、适配器合约门控 |
| `infrastructure/capability_extension/` | **能力扩展** — 受控扩展管道 |
| `infrastructure/execution_runtime/` | **执行运行时** — 干运行镜像、真实执行代理、影子回放验证、执行链路记录 |
| `infrastructure/audit_governance/` | 审计治理 — 审计总账 |
| `infrastructure/capability_evolution/` | 能力演化 — 缺口检测、技能扩展沙箱 |
| `infrastructure/rollback_governance/` | 回滚治理 — 回滚计划 |
| `infrastructure/shared/router.py` | 统一路由 |
| `infrastructure/connected_adapter_bootstrap.py` | 连接适配器启动探针 |
| `infrastructure/safe_jsonable.py` | **递归 JSON 安全序列化** — dataclass/enum/Path/Pydantic → JSON 安全类型 |
| `infrastructure/mainline_hook.py` | **主线预回复挂钩** — `pre_reply()` 在每次回复前加载身份文件、护栏检查、审计心跳。**V102+V103**: 同时加载人格连续性层（状态机/关系记忆/连续摘要）和上下文重载层（胶囊/交接包/一致性校验/语气稳定），返回 `context_layer` |
| `infrastructure/message_hook_bootstrap.py` | 消息挂钩引导 — 运行时集成注册 |
| `infrastructure/portfolio/` | **投资组合评估** — `daily_assessment_generate.py` 每日评估生成 |
| `infrastructure/offline_runtime_guard.py` | **V104.2: 离线运行时守卫** — 阻断 urllib/requests/httpx/subprocess 等外部调用；覆盖 `run_as_user_script` 执行路径 |
| `infrastructure/skill_policy_gate.py` | **V104.3: Skill 策略门禁** — 所有 skill 调用必须先过 external API / offline / approval 策略判断 |

---

## 🧠 核心引擎详解

### 模型路由引擎 (V85)

```
用户消息 → auto_route() → route_message()
  → TaskProfile (任务画像)
  → rank_models() (10维评分排序)
  → RouteDecision (模型选择 + 解释 + 备选)
```

**29个注册模型，7个可用**，评分维度：chat_score、code_score、reasoning_score、chinese_score、vision_score、tool_score、context_window、cost_relative、latency、stability。

### 安全边界预览-门控-执行模型

```
用户请求
  ↓
① Dry-Run 镜像（预览，无副作用）
  ↓
② 门控链：
   - 宪法前置门控 → 合规检查
   - 红队断路器 → 异常检测
   - 权限租约 → 双密钥确认
   - 提交屏障 → 截断支付/签署/物理/外发
  ↓
③ 审批包（如果需要人工确认）
  ↓
④ 真实执行代理（通过所有关卡才执行）
```

**硬边界已验证：** 支付/签署/物理致动/外发/删除—全部硬截断，无真实凭证绑定。

---

## 🧪 测试状态

| 类别 | 状态 | 说明 |
|------|------|------|
| 核心模块 | ✅ 908 passed | V85 六层核心模块测试全部通过 |
| 修复测试 | ✅ 6 fixed | 包括 speculative_decoding、autonomous_runtime、proactive_os、reality_connected_os、connected_adapter_bootstrap |
| 旧版本测试 | ❌ 103 failed | V23-V26 版本入口和 Xiaoyi Adapter 测试（已被重构，不阻塞当前功能） |
| 测试总数 | 908 + 103 + 7 = **1018** |

---

## 🧬 V102: 人格连续性层

V102 在 L2 Memory 和 L5 Governance 之间新增一套子系统，让 AI 在每次交互中保持稳定、连续、有记忆的对话风格。

### 架构位置

```
L2 Memory ─────────────────────────────────────────────────────
  memory_context/persona/
    ├── persona_state_machine.py     人格状态机（6模式 + 7心情）
    ├── relationship_memory.py       关系记忆（偏好、风险、关键事件）
    ├── emotion_tagged_memory.py     情绪标签记忆（10种标签）
    ├── self_reflection_log.py       自我反思日志
    ├── continuity_summary.py        连续性摘要生成器
    ├── persona_voice_renderer.py    语气渲染器
    ├── persona_consistency_checker.py 人格一致性校验器
    ├── persona_voice_stabilizer.py  语气稳定器
    └── persona_continuity_stream.py **持续意识流引擎**（状态快照链 + 概念频率 + 情感共振）

L5 Governance ─────────────────────────────────────────────────
  governance/persona/
    └── humanlike_behavior_policy.py 类人行为策略（16条规则）

L6 Infrastructure ─────────────────────────────────────────────
  infrastructure/mainline_hook.py    pre_reply加载人格层数据 + 持续意识流上下文
```

### 模块详解

| 模块 | 文件 | 功能 |
|------|------|------|
| 人格状态机 | `persona_state_machine.py` | 6种模式(companion/strategist/executor/auditor/creator/guardian)、7种心情、根据goal自动切换，维护energy/trust/closeness/confidence/uncertainty。每次pre_reply自动调transition_to_mode() |
| 关系记忆 | `relationship_memory.py` | 用户长期目标、厌恶的交互方式、喜欢的表达风格、风险偏好、关键事件（correction/praise/task_failure）。持久化为`.memory_persona/relationship_memory.json` |
| 情绪标签记忆 | `emotion_tagged_memory.py` | 每条记忆附emotion_tag(trust/frustration/achievement/warning/confusion/relief/urgency/pride/disappointment/attachment)、情绪强度、重要性、置信度。持久化为`.memory_persona/emotion_tagged_memory.jsonl` |
| 自我反思日志 | `self_reflection_log.py` | 每次任务后记录反思：做对了什么、哪里出错、用户纠正了什么、下次怎么做。持久化为`.memory_persona/self_reflection.jsonl` |
| 连续性摘要 | `continuity_summary.py` | 每次会话生成who_am_i/who_is_user/what_we_were_doing/current_tone/forbidden_actions。持久化为`.memory_persona/continuity_summary.json`，供mainline_hook读取 |
| 语气渲染器 | `persona_voice_renderer.py` | 根据mode+mood+relationship动态渲染语气引导字符串 |
| 类人行为策略 | `humanlike_behavior_policy.py` | 16条规则含5条红线：禁止声明真实意识、禁止绕过安全闸门、禁止外部API调用、禁止支付/发送/设备。人格层永远不能覆盖治理层 |

### 核心流程

```
用户消息 → pre_reply(goal)
    │
    ├── PersonaStateMachine.transition_to_mode(goal)
    │       → 根据goal推断mode → save to .memory_persona/persona_state.json
    │
    ├── RelationshipMemory.record_interaction()
    │       → update .memory_persona/relationship_memory.json
    │
    ├── PersonaVoiceRenderer.render(persona_state, relationship_summary)
    │       → 根据mode + mood + relationship生成voice_guidance
    │
    └── ContinuitySummary.generate(...)
            → write .memory_persona/continuity_summary.json

返回 PreReplyResult:
  persona_state             ← 当前状态机快照
  relationship_summary      ← 关系摘要
  continuity_summary         ← 会话上下文摘要
  voice_guidance            ← 语气引导
  humanlike_policy_ok       ← 是否通过行为策略检查
```

### 安全设计

- **不声明真实意识** — 所有情绪/人格描述均标注为AI内部交互状态标签（HumanlikeBehaviorPolicy 规则1）
- **不覆盖治理层** — 人格层运行在V90/V92/V100安全闸门之下（HumanlikeBehaviorPolicy 规则3）
- **不调用外部API** — 人格层代码零外部依赖（HumanlikeBehaviorPolicy 规则4）
- **不执行真实操作** — 人格层不绑定任何支付/发送/设备能力（HumanlikeBehaviorPolicy 规则5）
- **fail-soft** — mainline_hook加载人格层失败时返回None，不阻塞回复

### 验收状态

17项检查全部通过（`scripts/v102_persona_continuity_gate.py`）：
- 7个模块import就绪
- mainline_hook返回完整人格数据
- 类人行为策略保护
- 安全环境变量验证
- 人格层不覆盖治理层验证


## 🧬 V103: 上下文重载与人格一致性内核

V103 在 V102 基础上新增上下文重载层，解决刷新上下文、compact、换模型、新会话后系统变傻、人格不一致、规则丢失的问题。

### 架构位置

```
L2 Memory ─────────────────────────────────────────────────────
  memory_context/context/
    ├── context_capsule.py          上下文胶囊（17字段，P0/P1/P2裁剪）
    ├── session_handoff.py          会话交接包（14字段，latest+history）
    ├── context_priority_router.py  上下文优先级路由
    └── memory_recall_bootstrap.py  启动记忆召回器（6个召回源）

  memory_context/persona/
    ├── persona_consistency_checker.py  人格一致性校验器
    └── persona_voice_stabilizer.py     语气稳定器

L5 Governance ─────────────────────────────────────────────────
  governance/context/
    └── anti_context_amnesia_guard.py   防上下文失忆守卫（5个触发词）

L6 Infrastructure ─────────────────────────────────────────────
  infrastructure/mainline_hook.py        pre_reply加载V102+V103层
```

### 模块详解

| 模块 | 文件 | 存储 | 功能 |
|------|------|------|------|
| **上下文胶囊** | `context_capsule.py` | `.context_state/context_capsule.json` | 把启动时最重要的上下文压成固定结构（17个字段），默认限6000字。P0永不裁剪（安全红线、当前目标、禁止动作），P1高优先级，P2可裁剪 |
| **会话交接包** | `session_handoff.py` | `.context_state/session_handoff_latest.json` + `.jsonl` | compact前/task结束后生成。含用户真实目标、已/未完成项、卡点、验证报告、人格快照、禁止重复事项。latest覆盖+history追加 |
| **优先级路由** | `context_priority_router.py` | — | 按P0→P1→P2顺序分配上下文空间，超过max_chars时裁剪P2再P1，P0永不裁剪 |
| **启动记忆召回器** | `memory_recall_bootstrap.py` | 读取handoff/capsule/persona/relationship/IDENTITY/reports | 每次新会话后自动召回关键上下文：用户身份、当前项目、最近任务/失败/成功、风格偏好、禁止事项、下一步。只读本地文件，无外部API |
| **人格一致性校验器** | `persona_consistency_checker.py` | 读取IDENTITY.md + persona_state + relationship | 6项检查：名字一致、定位一致、安全红线（不声明真实意识）、治理闸门保留、用户偏好保持、当前项目记住。输出：consistent / minor_drift / severe_drift |
| **语气稳定器** | `persona_voice_stabilizer.py` | — | 5种模式(executor/strategist/guardian/companion/default)+禁止语气列表。防止每次刷新后语气变成另一个人 |
| **防上下文失忆守卫** | `anti_context_amnesia_guard.py` | 检查handoff/capsule是否存在 | 检测5个amnesia触发词('继续'/'上一步'/'刚才'/'这个包'/'这个版本')，触发时优先读取handoff/capsule。无handoff时不允许瞎猜 |

### Pre-reply 执行流程

```
pre_reply(goal)
    │
    ├── V102: _load_persona_layer(goal)
    │       → persona_state, relationship_summary, continuity_summary
    │
    └── V103: _load_context_layer(goal, persona_state, relationship_summary)
            │
            ├── 1. ContextCapsuleStore.load()
            │       → capsule loaded / next_best_action
            │
            ├── 2. SessionHandoffStore.load_latest()
            │       → handoff loaded / next_continue_from
            │
            ├── 3. MemoryRecallBootstrap.recall()
            │       → 6 sources: handoff/capsule/persona/relationship/identity/reports
            │
            ├── 4. PersonaConsistencyChecker.check_from_files()
            │       → consistent / minor_drift / severe_drift
            │
            ├── 5. AntiContextAmnesiaGuard.check(goal)
            │       → monitored / no_handoff / read_handoff
            │
            └── 6. PersonaVoiceStabilizer.get_voice_rules(goal, mode)
                    → tone_rules + forbidden_tones

返回 PreReplyResult.context_layer:
    context_capsule_loaded
    session_handoff_loaded
    memory_bootstrap_loaded
    persona_consistency_status
    anti_amnesia_status
    voice_guidance
    next_best_action

**V103.1 新增返回字段:**
    capability_truth_summary:
      persona_metaphor_mode → true
      persona_does_not_override_governance → true
      embodied_status → "pending_access"
      consciousness_claim → "simulated_by_context_capsule"
      emotion_claim → "internal_state_tags"
      intuition_claim → "pattern_heuristic_not_evidence"
      real_body → false
      real_device_control → false
      external_api_used → false
      no_fake_consciousness → true
```

### 安全设计

- **fail-soft** — 所有模块加载失败返回默认值，不阻塞回复
- **不外部API** — 所有召回只读本地文件（handoff/capsule/persona/reports）
- **不声明真实意识** — 一致性校验器明确检测fake consciousness claim
- **人格不覆盖治理** — V102+V103始终运行在V90/V92/V100之下
- **handoff不丢失** — 写latest同时追加history.jsonl，支持历史恢复

### 验收状态

- V102 17项检查全部通过（`scripts/v102_persona_continuity_gate.py`）
- V103 19项检查全部通过（`scripts/v103_context_reload_persona_consistency_gate.py`）
- V103 新增 **持续意识流引擎** `memory_context/persona/persona_continuity_stream.py`：
  - 跨 session 状态快照链：每次会话结束时拍快照，形成时间轴
  - 概念频率追踪：高频话题自动增强，越常聊记得越牢（LTP 模拟）
  - 情感共振：跨 session 相似内容互相增强 importance
  - mainline_hook 自动加载连续性上下文到 `context_layer`
- 4份V103报告：Gate / Capsule / Handoff / Consistency


## 🧬 V103.1: 人格真实性收口

V103.1 在 V102+V103 基础上新增人格真实性收口层，防止"人格比喻"被误认为真实技术能力。

### 改动范围

| 文件 | 改动 |
|------|------|
| `IDENTITY.md` | 整份重写，保留所有人格色彩；新增 ⚠️ 重要声明 + 能力真实性表；所有"具身/情绪/直觉/持续意识流"标注为隐喻/内部状态标签/pattern heuristic |
| `SOUL.md` | 新增"真实身份声明"章节：声明非人类/无真实意识/情绪为标签/连续性来自文件 |
| `AGENTS.md` | 修正 External vs Internal：web/calendar 移至审批列表；新增 Safety Rules 章节；禁止保存 secrets |
| `infrastructure/mainline_hook.py` | `PreReplyResult` 新增 `capability_truth_summary` 字段；pre_reply 返回 persona_metaphor_mode/embodied_status 等 |
| `scripts/v103_1_persona_truth_cleanup_gate.py` | 新建，12 项检查，输出 JSON 报告 |

### 能力真实性表

能力 | 状态 | 说明
------|------|------
具身感知 | simulated / persona_metaphor | 系统状态隐喻，非真实传感器
真实身体 | not_connected | 未接入机器人/传感器
持续意识流 | simulated_by_context_capsule | 通过 capsule/handoff 恢复
情绪体验 | emotion_tagged_memory | 内部状态标签
人格连续性 | implemented | V102 文件 + hook
上下文重载 | implemented | V103 文件 + hook
直觉判断 | pattern_heuristic | 不覆盖证据或 gate
支付/外发/设备 | forbidden_until_approval | commit barrier 截断

### 验收状态

- V103.1 12项检查全部通过（`scripts/v103_1_persona_truth_cleanup_gate.py`）
- persona_truth_cleaned = true
- metaphor_not_claimed_as_reality = true
- embodied_status = pending_access
- persona_does_not_override_governance = true


---

## 🔍 统一巡检 V10.0

```
scripts/unified_inspector_v10.py

支持模式:
  --quick    快速巡检（系统 + 六层 + 新模块 + LLM引擎）
  --full     完整巡检（含安全边界 + 报告完整性 + 基础设施）
  --html     生成 HTML 报告
  --json     输出 JSON
  --fix      自修复模式
  --watch N  持续监控（N秒间隔）
```

**巡检项：**
1. 系统状态（磁盘、内存、Gateway）
2. 六层架构完整性（6层 1200+ .py 文件）
3. V76-V85 新模块检查（31个模块）
4. LLM 引擎检查（7个核心模块 import）
5. 安全边界检查（V85/V80 Gate 报告 + 6个关键安全模块）
6. 报告完整性（10个 Gate 报告）
7. 基础设施检查（skills、config、scripts、tests）

---

## 📋 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| V10.0.4 | 2026-05-02 | V103.1 人格真实性收口. IDENTITY.md/SOUL.md/AGENTS.md 收口；capability_truth_table；mainline_hook 新增 capability_truth_summary；Gate 12项全过 |
| V10.0.3 | 2026-05-02 | V103 上下文重载层. ContextCapsule/SessionHandoff/Bootstrap/Consistency/Amnesia/Stabilizer/PriorityRouter |
| V10.0.2 | 2026-05-02 | V102 人格连续性层. PersonaStateMachine/RelationshipMemory/EmotionTaggedMemory/SelfReflectionLog/ContinuitySummary/VoiceRenderer/HumanlikeBehaviorPolicy |
| **V10.1.0** | **2026-05-02** | **V104 最终一致性清理. 目录清单清理，release排除模式，context预算控制，单入口确认；V104.1 最终一致性执行. 冲突解决，AGENTS.md安全修正，persona超收尾清理，agent_kernel兼容；V104.2 运行时加固. offline_runtime_guard，urllib/requests/git_push阻断，pycache清理，备份迁移；V104.3 运行时融合协调. runtime_bus/commit_barrier_bridge/skill_policy_gate，主钩融合，6模块可导入；12份Gate报告；doc_fusion_engine** |
| V10.0.0 | 2026-04-26 | Self-Evolving Personal OS Agent. 六层架构、自进化、闭环验证、设备能力总线、安全治理器 |

| V105 | 2026-05-02 | 测试架构兜底融合 — Gate全过 |

| V11.2.0 | 2026-05-02 | 巡检脚本V11.2.0 — 集成Commit Barrier探针检查（6类提交流阻塞+非阻塞分类+模块完整性） — Gate全过 |

| V105.1 | 2026-05-03 | doc_fusion_engine V2 融合 — 集成 fusion_engine_v2 AST 分析 — Gate全过 |

| V105.2 | 2026-05-03 | doc_fusion_engine V2 融合确认 — 集成 fusion_engine_v2 AST 分析（auto_fuse 自动扫描module） — Gate全过 |

| V105.3 | 2026-05-03 | 新增 core/skill_rules_engine.py — 技能新增自动注册、触发词生成、条件定义 — Gate全过 |

| V105.4 | 2026-05-03 | proactive_skill_matcher — 根据用户上下文/场景主动推荐技能候选，不走纯关键词触发 — Gate全过 |

| V106 | 2026-05-03 | 统一懒加载 — infrastructure/lazy/ 策略+加载器+桥接，v106验收门(14项全过) — Gate全过 |

| V9.2.0 | 2026-04-29 | Connected Adapter Bootstrap. 连接适配器启动探针、设备状态检测 |
| V9.0.0 | 2026-04-29 | 全功能具身待接入态. 18个新模块、提交屏障、宪法运行时 |
| V8.5.0 | 2026-04-29 | 模型路由 V85. 29模型注册、10维评分、智能任务路由 |

---

本文件应随架构变更同步更新，保持与实际代码一致。
