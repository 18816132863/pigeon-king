# 🚀 鸽子王 V10 快速上手指南

> 5 分钟带你了解这个系统能做什么、怎么用。

---

## 这是什么？

**鸽子王 V10** 是一个运行在 OpenClaw 平台上的自进化个人 OS 代理。它有自己的模型路由引擎、记忆系统、安全治理层，可以帮你完成各种任务。

---

## 基本使用

### 直接聊天

就像正常聊天一样。你可以：

```
帮我查一下今天天气
设置一个明早8点的闹钟
搜索我的笔记
帮我分析这段代码
```

系统会自动决定用哪个模型来处理你的请求。

### 用 / 命令

| 命令 | 作用 |
|------|------|
| `/new` 或 `/reset` | 重置会话上下文 |
| `/status` | 查看当前会话状态和模型信息 |
| `/reasoning` | 开启/关闭思考过程显示 |

### 发送文件

支持发送图片进行分析。直接发图片，系统会自动识别和理解内容。

---

## 系统巡检

```
python3 scripts/unified_inspector_v10.py --quick   # 快速巡检
python3 scripts/unified_inspector_v10.py --full    # 完整巡检（含安全边界）
python3 scripts/unified_inspector_v10.py --html    # 快速+生成HTML报告
```

巡检会检查：系统状态、六层架构完整性、V76-V85 新模块、LLM 引擎、安全边界门控。

---

## 运行测试

```bash
# 运行所有测试
python3 -m pytest tests/ -q

# 运行特定测试
python3 -m pytest tests/test_v10_2_autonomous_runtime.py -v

# 跳过已知失败的旧版本测试
python3 -m pytest tests/ -q --ignore=tests/test_v23_2_real_work_entry.py
```

当前测试状态：908 passed / 103 known-failing（旧版本入口测试）

---

## 目录结构速览

```
workspace/
├── core/            # 核心 - LLM引擎、自主决策、授权授权
│   ├── llm/         #   模型路由引擎
│   └── autonomy/    #   自主决策框架
├── orchestration/   # 编排 - 任务规划、路由、工作流
│   ├── router/      #   模型和技能路由
│   ├── planner/     #   任务规划器
│   └── workflows/   #   业务工作流
├── governance/      # 治理 - 安全、宪法、审计
│   ├── constitutional_runtime/  # 宪法运行时
│   ├── embodied_pending_state/  # 具身待接入（安全边界）
│   └── red_team_safety/         # 红队安全测试
├── execution/       # 执行 - 工具绑定、视觉操作、推测解码
├── infrastructure/  # 基础设施 - 平台适配、存储、联网
└── memory_context/  # 记忆 - 知识图谱、向量搜索、学习循环
```

---

## 关键限制

| 能力 | 状态 |
|------|------|
| 支付/签署 | ❌ 硬截断 - 不会真实执行 |
| 物理致动 | ❌ 硬截断 |
| 外发消息 | ❌ 只生成审批包 |
| 删除操作 | ❌ 硬截断 |
| 身份承诺 | ❌ 硬截断 |
| 搜索/查询/分析 | ✅ 正常 |
| 调用手机功能（闹钟、备忘录等） | ✅ 正常 |
| 文件操作 | ✅ 正常 |

---

## 遇到问题？

先跑巡检：
```bash
python3 scripts/unified_inspector_v10.py --quick
```

如果你需要更详细的文档：
- [V10 架构总览](ARCHITECTURE_V10.md)
- [配置指南](configuration.md)
- [运行手册](runbook.md)
