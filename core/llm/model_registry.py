"""V85 model registry: single source of truth for all model metadata."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

from core.llm.decision_matrix import rank_models, score_model
from core.llm.schemas import (
    Complexity,
    CostPreference,
    LatencyPreference,
    ModelInfo,
    ModelType,
    PrivacyLevel,
    Provider,
    RouteDecision,
    TaskCategory,
    TaskProfile,
)


class ModelRegistry:
    _instance: Optional["ModelRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._models: Dict[str, ModelInfo] = {}
        self._aliases: Dict[str, str] = {}
        self._custom_classifiers: List[Callable[[TaskProfile, Dict[str, Any]], Optional[str]]] = []
        self._register_defaults()
        self.load_external_registry()

    # ------------------------------------------------------------------
    # Built-in models.  These are only metadata.  Availability is updated
    # by model_discovery without ever printing or hard-coding secrets.
    # ------------------------------------------------------------------
    def _register_defaults(self) -> None:
        defaults = [
            # Local / internal routes
            dict(name="LLM_ROUTER", provider="xiaoyi", label="小艺 LLM 路由器", capabilities=["chat", "vision", "tool_calling", "json", "low_cost"], chat_score=7, chinese_score=8, business_score=6, multimodal_score=6, tool_use_score=7, json_score=6, supports_vision=True, supports_function_calling=True, context_window=196000, cost_relative=0.2, latency_relative=0.5, stability_score=7, privacy_score=8, fallback_group="fast_low_cost", available=True, source="builtin"),
            dict(name="pigeon-king-speculative", provider="xiaoyi", label="鸽子王投机解码", capabilities=["chat", "fast"], chat_score=6, chinese_score=7, context_window=196000, cost_relative=0.2, latency_relative=0.25, stability_score=6, privacy_score=8, fallback_group="fast_low_cost", available=True, source="builtin"),
            dict(name="XIAOYI_IMAGE_TOOL", provider="xiaoyi", label="小艺图像生成/编辑工具", model_type="image_generation", capabilities=["image_generation", "tool_calling"], chat_score=5, multimodal_score=8, tool_use_score=8, context_window=32000, cost_relative=0.5, latency_relative=1.2, stability_score=7, privacy_score=8, fallback_group="image_generation", available=True, source="builtin"),
            dict(name="XIAOYI_VIDEO_TOOL", provider="xiaoyi", label="小艺视频生成工具", model_type="video_generation", capabilities=["video_generation", "tool_calling"], chat_score=5, multimodal_score=8, tool_use_score=8, context_window=32000, cost_relative=1.0, latency_relative=2.0, stability_score=6, privacy_score=8, fallback_group="video_generation", available=True, source="builtin"),

            # DeepSeek
            dict(name="deepseek-chat", provider="deepseek", label="DeepSeek Chat / V3", capabilities=["chat", "coding", "tool_calling", "json", "chinese"], chat_score=8, code_score=8, reasoning_score=7, chinese_score=9, business_score=8, tool_use_score=8, json_score=7, context_window=65536, supports_function_calling=True, supports_json_mode=True, cost_relative=0.3, latency_relative=0.8, stability_score=8, api_key_env="DEEPSEEK_API_KEY", fallback_group="chinese_business", best_for=["中文商业", "编程", "低成本通用"], available=False),
            dict(name="deepseek-reasoner", provider="deepseek", label="DeepSeek Reasoner / R1", model_type="reasoning", capabilities=["reasoning", "coding", "chinese"], chat_score=5, code_score=7, reasoning_score=10, chinese_score=8, business_score=7, tool_use_score=4, json_score=5, context_window=65536, cost_relative=0.5, latency_relative=2.0, stability_score=7, api_key_env="DEEPSEEK_API_KEY", fallback_group="reasoning_high", best_for=["复杂推理", "逻辑分析", "规划决策"], available=False),

            # OpenAI
            dict(name="gpt-4o", provider="openai", label="GPT-4o", capabilities=["chat", "vision", "coding", "tool_calling", "json", "multilingual"], chat_score=9, code_score=9, reasoning_score=8, chinese_score=8, business_score=8, multimodal_score=9, tool_use_score=9, json_score=9, long_context_score=8, context_window=128000, supports_vision=True, supports_function_calling=True, supports_json_mode=True, cost_relative=2.0, latency_relative=1.2, stability_score=9, privacy_score=6, api_key_env="OPENAI_API_KEY", fallback_group="vision_high", available=False),
            dict(name="gpt-4.1", provider="openai", label="GPT-4.1", capabilities=["chat", "vision", "coding", "tool_calling", "json", "long_context", "multilingual"], chat_score=9, code_score=9, reasoning_score=9, chinese_score=8, business_score=8, multimodal_score=8, tool_use_score=9, json_score=9, long_context_score=10, context_window=1000000, supports_vision=True, supports_function_calling=True, supports_json_mode=True, cost_relative=1.6, latency_relative=1.2, stability_score=9, privacy_score=6, api_key_env="OPENAI_API_KEY", fallback_group="reasoning_high", available=False),
            dict(name="gpt-4.1-mini", provider="openai", label="GPT-4.1 Mini", capabilities=["chat", "vision", "coding", "tool_calling", "json", "long_context"], chat_score=8, code_score=8, reasoning_score=7, chinese_score=7, business_score=7, multimodal_score=7, tool_use_score=8, json_score=8, long_context_score=10, context_window=1000000, supports_vision=True, supports_function_calling=True, supports_json_mode=True, cost_relative=0.55, latency_relative=0.8, stability_score=8, privacy_score=6, api_key_env="OPENAI_API_KEY", fallback_group="long_context_high", available=False),
            dict(name="gpt-4o-mini", provider="openai", label="GPT-4o Mini", capabilities=["chat", "vision", "tool_calling", "json"], chat_score=7, code_score=7, reasoning_score=6, chinese_score=7, business_score=7, multimodal_score=7, tool_use_score=7, json_score=8, long_context_score=8, context_window=128000, supports_vision=True, supports_function_calling=True, supports_json_mode=True, cost_relative=0.4, latency_relative=0.7, stability_score=8, privacy_score=6, api_key_env="OPENAI_API_KEY", fallback_group="fast_low_cost", available=False),
            dict(name="o3-mini", provider="openai", label="o3-mini", model_type="reasoning", capabilities=["reasoning", "coding"], chat_score=4, code_score=8, reasoning_score=10, chinese_score=7, business_score=6, context_window=200000, cost_relative=1.4, latency_relative=2.5, stability_score=8, api_key_env="OPENAI_API_KEY", fallback_group="reasoning_high", available=False),
            dict(name="o4-mini", provider="openai", label="o4-mini", model_type="reasoning", capabilities=["reasoning", "coding"], chat_score=5, code_score=8, reasoning_score=10, chinese_score=7, business_score=6, context_window=200000, cost_relative=1.2, latency_relative=2.2, stability_score=8, api_key_env="OPENAI_API_KEY", fallback_group="reasoning_high", available=False),

            # Anthropic
            dict(name="claude-sonnet-4-20250514", provider="anthropic", label="Claude Sonnet 4", capabilities=["chat", "vision", "coding", "tool_calling", "json", "long_context"], chat_score=9, code_score=10, reasoning_score=9, chinese_score=7, business_score=7, multimodal_score=8, tool_use_score=10, json_score=8, long_context_score=9, context_window=200000, supports_vision=True, supports_function_calling=True, supports_json_mode=True, cost_relative=3.0, latency_relative=1.5, stability_score=9, api_key_env="ANTHROPIC_API_KEY", fallback_group="coding_high", available=False),
            dict(name="claude-opus-4", provider="anthropic", label="Claude Opus 4", capabilities=["chat", "vision", "coding", "tool_calling", "json", "long_context", "reasoning"], chat_score=9, code_score=10, reasoning_score=10, chinese_score=7, business_score=7, multimodal_score=8, tool_use_score=10, json_score=8, long_context_score=9, context_window=200000, supports_vision=True, supports_function_calling=True, supports_json_mode=True, cost_relative=5.0, latency_relative=2.0, stability_score=9, api_key_env="ANTHROPIC_API_KEY", fallback_group="reasoning_high", available=False),

            # Google / Gemini
            dict(name="gemini-2.5-pro", provider="gemini", label="Gemini 2.5 Pro", capabilities=["chat", "vision", "reasoning", "long_context", "tool_calling", "json"], chat_score=9, code_score=8, reasoning_score=9, chinese_score=7, business_score=7, multimodal_score=9, tool_use_score=8, json_score=8, long_context_score=10, context_window=1000000, supports_vision=True, supports_function_calling=True, supports_json_mode=True, cost_relative=1.8, latency_relative=1.6, stability_score=8, api_key_env="GEMINI_API_KEY", fallback_group="long_context_high", available=False),
            dict(name="gemini-2.5-flash", provider="gemini", label="Gemini 2.5 Flash", capabilities=["chat", "vision", "long_context", "json", "fast"], chat_score=8, code_score=7, reasoning_score=7, chinese_score=7, business_score=7, multimodal_score=8, tool_use_score=7, json_score=8, long_context_score=9, context_window=1000000, supports_vision=True, supports_json_mode=True, cost_relative=0.35, latency_relative=0.55, stability_score=8, api_key_env="GEMINI_API_KEY", fallback_group="fast_low_cost", available=False),

            # Chinese providers
            dict(name="qwen-max", provider="qwen", label="通义千问 Max", capabilities=["chat", "coding", "chinese", "tool_calling", "json"], chat_score=8, code_score=8, reasoning_score=8, chinese_score=9, business_score=9, tool_use_score=7, json_score=8, context_window=32768, supports_function_calling=True, supports_json_mode=True, cost_relative=0.5, latency_relative=0.8, stability_score=8, api_base="https://dashscope.aliyuncs.com/compatible-mode/v1", api_key_env="QWEN_API_KEY", provider_extra="qwen", fallback_group="chinese_business", available=False),
            dict(name="qwen-plus", provider="qwen", label="通义千问 Plus", capabilities=["chat", "chinese", "long_context", "json"], chat_score=7, code_score=6, reasoning_score=6, chinese_score=9, business_score=8, json_score=7, long_context_score=9, context_window=131072, supports_json_mode=True, cost_relative=0.3, latency_relative=0.6, stability_score=8, api_base="https://dashscope.aliyuncs.com/compatible-mode/v1", api_key_env="QWEN_API_KEY", fallback_group="chinese_business", available=False),
            dict(name="qwen-turbo", provider="qwen", label="通义千问 Turbo", capabilities=["chat", "chinese", "fast", "low_cost"], chat_score=6, code_score=5, reasoning_score=5, chinese_score=8, business_score=7, context_window=131072, cost_relative=0.1, latency_relative=0.35, stability_score=7, api_base="https://dashscope.aliyuncs.com/compatible-mode/v1", api_key_env="QWEN_API_KEY", fallback_group="fast_low_cost", available=False),
            dict(name="moonshot-v1-128k", provider="kimi", label="Kimi 128K", capabilities=["chat", "chinese", "long_context", "document"], chat_score=7, code_score=6, reasoning_score=6, chinese_score=9, business_score=8, long_context_score=9, context_window=128000, cost_relative=0.5, latency_relative=0.8, stability_score=7, api_key_env="MOONSHOT_API_KEY", fallback_group="long_context_high", available=False),
            dict(name="LLM_GLM5", provider="zhipu", label="GLM-5", capabilities=["chat", "vision", "chinese", "tool_calling", "json", "long_context"], chat_score=8, code_score=7, reasoning_score=7, chinese_score=9, business_score=8, multimodal_score=8, tool_use_score=7, json_score=7, long_context_score=9, context_window=131072, supports_vision=True, supports_function_calling=True, supports_json_mode=True, cost_relative=0.6, latency_relative=0.9, stability_score=7, api_base="https://open.bigmodel.cn/api/paas/v4", api_key_env="GLM_API_KEY", fallback_group="vision_high", available=False),
            dict(name="LLM_GLM4_Flash", provider="zhipu", label="GLM-4 Flash", capabilities=["chat", "chinese", "fast", "low_cost"], chat_score=6, code_score=5, reasoning_score=5, chinese_score=8, business_score=7, context_window=128000, cost_relative=0.05, latency_relative=0.45, stability_score=7, api_base="https://open.bigmodel.cn/api/paas/v4", api_key_env="GLM_API_KEY", fallback_group="fast_low_cost", available=False),
            dict(name="doubao-pro-128k", provider="doubao", label="豆包 Pro 128K", capabilities=["chat", "chinese", "long_context"], chat_score=7, code_score=6, reasoning_score=6, chinese_score=9, business_score=8, long_context_score=8, context_window=128000, cost_relative=0.3, latency_relative=0.65, stability_score=7, api_base="https://ark.cn-beijing.volces.com/api/v3", api_key_env="DOUBAO_API_KEY", fallback_group="chinese_business", available=False),

            # Local / compatible
            dict(name="local-openai-compatible", provider="local", label="本地 OpenAI 兼容模型", capabilities=["chat", "privacy", "low_cost"], chat_score=6, code_score=5, reasoning_score=5, chinese_score=6, business_score=5, privacy_score=10, context_window=32768, cost_relative=0.05, latency_relative=0.7, stability_score=6, api_base="http://localhost:11434/v1", api_key_env="LOCAL_LLM_API_KEY", fallback_group="privacy_local", available=False),
        ]
        for item in defaults:
            item.pop("provider_extra", None)
            self.add_model(ModelInfo.from_dict(item))

    @property
    def data_dir(self) -> Path:
        return Path(__file__).resolve().parent / "data"

    def load_external_registry(self) -> None:
        """Load model_registry.json, custom_models.json and optional YAML manifests."""
        paths = [
            self.data_dir / "model_registry.json",
            Path(__file__).resolve().parent / "custom_models.json",
            Path(__file__).resolve().parent / "models_override.json",
        ]
        for path in paths:
            self._load_json_models(path)
        self._load_yaml_models(self.data_dir / "manual_manifest.yaml")

    def _load_json_models(self, path: Path) -> None:
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            items = data.get("models", data) if isinstance(data, dict) else data
            if not isinstance(items, list):
                return
            for item in items:
                if isinstance(item, dict) and item.get("name"):
                    model = ModelInfo.from_dict({**item, "source": str(path)})
                    self.add_model(model)
        except Exception as exc:
            print(f"[ModelRegistry] skip invalid registry {path}: {exc}")

    def _load_yaml_models(self, path: Path) -> None:
        if not path.exists():
            return
        try:
            import yaml  # type: ignore
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            items = data.get("models", []) if isinstance(data, dict) else []
            for item in items:
                if isinstance(item, dict) and item.get("name"):
                    self.add_model(ModelInfo.from_dict({**item, "source": str(path)}))
        except Exception:
            # YAML support is optional.  JSON custom_models remains the stable path.
            return

    def save_snapshot(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        path = self.data_dir / "model_registry.snapshot.json"
        payload = {"models": [m.to_dict() for m in self.list_models(available_only=False)]}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def add_model(self, model: ModelInfo) -> None:
        self._models[model.name] = model
        self._aliases[model.label] = model.name
        self._aliases[model.name.lower()] = model.name

    def add_alias(self, alias: str, model_name: str) -> None:
        if model_name in self._models:
            self._aliases[alias] = model_name
            self._aliases[alias.lower()] = model_name

    def get_model(self, name_or_alias: str) -> Optional[ModelInfo]:
        if not name_or_alias:
            return None
        if name_or_alias in self._models:
            return self._models[name_or_alias]
        return self._models.get(self._aliases.get(name_or_alias) or self._aliases.get(name_or_alias.lower()))

    def list_models(self, available_only: bool = True) -> List[ModelInfo]:
        models = list(self._models.values())
        if available_only:
            models = [m for m in models if m.available]
        return sorted(models, key=lambda m: (m.provider.value, m.name))

    def list_by_provider(self, provider: Provider) -> List[ModelInfo]:
        return [m for m in self.list_models(True) if m.provider == provider]

    def list_by_category(self, category: TaskCategory) -> List[ModelInfo]:
        task = TaskProfile(category=category)
        return [m for m, _, _ in rank_models(self.list_models(True), task)]

    def register_classifier(self, fn: Callable[[TaskProfile, Dict[str, Any]], Optional[str]]) -> None:
        self._custom_classifiers.append(fn)

    def select(self, task: TaskProfile, context: Optional[Dict[str, Any]] = None) -> ModelInfo:
        context = context or {}
        for classifier in self._custom_classifiers:
            result = classifier(task, context)
            if result:
                model = self.get_model(result)
                if model and model.available:
                    return model

        ranked = rank_models(self.list_models(True), task, context)
        if ranked:
            return ranked[0][0]

        # Safe fallback: internal router first, then any registered model.
        fallback = self.get_model("LLM_ROUTER")
        if fallback:
            return fallback
        return list(self._models.values())[0]

    def select_multi(self, task: TaskProfile, top_k: int = 3, context: Optional[Dict[str, Any]] = None) -> List[ModelInfo]:
        ranked = rank_models(self.list_models(True), task, context)
        return [item[0] for item in ranked[:top_k]]

    def score(self, model: ModelInfo, task: TaskProfile, context: Optional[Dict[str, Any]] = None):
        return score_model(model, task, context)

    def explain(self, task: TaskProfile, selected: ModelInfo) -> str:
        reasons: List[str] = []
        if task.category in {TaskCategory.ARCHITECTURE, TaskCategory.REASONING, TaskCategory.PLANNING, TaskCategory.COMPLIANCE}:
            reasons.append("任务需要高质量推理")
        if task.requires_coding:
            reasons.append(f"需要代码/架构能力，代码评分 {selected.code_score}/10")
        if task.requires_long_context:
            reasons.append(f"需要长上下文，模型窗口 {selected.context_window}")
        if task.requires_vision:
            reasons.append("需要视觉理解")
        if task.requires_tool_calling:
            reasons.append("需要工具/外部能力协同")
        if task.cost_preference == CostPreference.LOW:
            reasons.append(f"成本优先，成本指数 {selected.cost_relative}")
        if task.category == TaskCategory.ECOMMERCE:
            reasons.append(f"中文电商任务，中文/商业评分 {selected.chinese_score}/{selected.business_score}")
        if not reasons:
            reasons.append("综合能力、成本、延迟、稳定性评分最优")
        return f"【模型路由】选择 {selected.label}：" + "；".join(reasons)


registry = ModelRegistry()

# Backward-compatible aliases used by old imports.
Cost = CostPreference
Latency = LatencyPreference
