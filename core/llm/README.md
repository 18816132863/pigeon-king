# V85 模型决策引擎 / Model Decision Engine

目标：收到消息后先识别任务场景，再根据模型能力、质量、成本、延迟、稳定性、上下文、隐私约束自动选择模型，并提供失败切换。

## 正确调用方式

```python
from core.llm import init_model_system, auto_route, call

init_model_system()

decision = auto_route("检查这个压缩包里的模型决策引擎")
print(decision.to_dict())

result = call([
    {"role": "user", "content": "帮我写一个函数"}
])
```

业务模块不要直接调用某个厂商 API，应统一走：

```python
from core.llm import call
```

或者：

```python
from core.llm.llm_gateway import LLMGateway
LLMGateway().call(messages)
```

## 核心文件

```text
schemas.py             统一数据结构
scene_classifier.py    消息场景识别
decision_matrix.py     决策矩阵评分
model_registry.py      模型注册表
model_discovery.py     自动发现与可用性管理
model_router.py        路由入口
llm_gateway.py         统一模型调用与失败切换
telemetry/             路由和调用日志
```

## 决策矩阵

总分 = 能力匹配 35% + 质量 20% + 成本 15% + 延迟 10% + 稳定性 10% + 上下文 5% + 隐私 5%。

高复杂度任务自动提高质量权重；低成本任务提高成本权重；隐私任务提高隐私权重。

## 硬约束

- 图片/截图：必须支持 vision。
- 工具调用：优先支持 function/tool calling。
- JSON 输出：优先支持 JSON mode/schema。
- 长文档/压缩包/多文件：优先长上下文；超限应转 RAG。
- 隐私：优先本地或高隐私分模型。
- 生成图/生成视频：不能走普通聊天模型。

## 新增模型

优先用 `core/llm/custom_models.json` 或 `core/llm/data/manual_manifest.yaml`，不要改主流程。

```json
[
  {
    "name": "my-model",
    "provider": "openai_compatible",
    "label": "我的模型",
    "capabilities": ["chat", "coding", "json"],
    "code_score": 8,
    "reasoning_score": 7,
    "context_window": 131072,
    "api_base": "https://example.com/v1",
    "api_key_env": "MY_MODEL_API_KEY",
    "fallback_group": "coding_high"
  }
]
```

## 日志

默认写入：

```text
~/.openclaw/model_router_logs/routes.jsonl
~/.openclaw/model_router_logs/calls.jsonl
```
