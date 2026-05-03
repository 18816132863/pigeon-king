"""
V85 Model Decision Engine schemas.

This module is intentionally dependency-free.  It defines the single data
contract used by the registry, scene classifier, decision matrix, router and
LLM gateway.  Business modules should not invent their own model objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskCategory(str, Enum):
    CHAT = "chat"
    REWRITE = "rewrite"
    SUMMARY = "summary"
    TRANSLATION = "translation"
    EXTRACTION = "extraction"
    WRITING = "writing"
    BUSINESS = "business_strategy"
    ECOMMERCE = "ecommerce_copywriting"
    COMPLIANCE = "compliance_check"
    ARCHITECTURE = "architecture_design"
    CODE = "coding"
    DEBUGGING = "debugging"
    MULTI_FILE_REFACTOR = "multi_file_refactor"
    REASONING = "complex_reasoning"
    PLANNING = "planning"
    SEARCH = "real_time_research"
    DOCUMENT = "document_analysis"
    DATA = "data_analysis"
    VISION = "vision_analysis"
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    AUDIO = "audio_processing"
    DEVICE_CONTROL = "device_control"
    AGENT = "agent_execution"
    AUDIT = "audit_review"


class Complexity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class CostPreference(str, Enum):
    LOW = "low"
    BALANCED = "balanced"
    PREMIUM = "premium"


class LatencyPreference(str, Enum):
    REALTIME = "realtime"
    BALANCED = "balanced"
    WAITABLE = "waitable"


class PrivacyLevel(str, Enum):
    NORMAL = "normal"
    SENSITIVE = "sensitive"
    PRIVATE = "private"


class Provider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    KIMI = "kimi"
    ZHIPU = "zhipu"
    DOUBAO = "doubao"
    BAICHUAN = "baichuan"
    YI = "yi"
    XIAOYI = "xiaoyi"
    LOCAL = "local"
    OPENAI_COMPATIBLE = "openai_compatible"
    CUSTOM = "custom"


class ModelType(str, Enum):
    CHAT = "chat"
    REASONING = "reasoning"
    CODING = "coding"
    VISION = "vision"
    IMAGE_GENERATION = "image_generation"
    VIDEO_GENERATION = "video_generation"
    AUDIO = "audio"
    EMBEDDING = "embedding"
    RERANK = "rerank"


@dataclass
class ModelInfo:
    """Unified model metadata used by the decision engine."""

    name: str
    provider: Provider
    label: str
    model_type: ModelType = ModelType.CHAT

    # Capabilities as explicit booleans.  Scores remain useful for ranking.
    capabilities: List[str] = field(default_factory=list)
    best_for: List[str] = field(default_factory=list)
    not_good_for: List[str] = field(default_factory=list)

    chat_score: int = 6
    code_score: int = 5
    reasoning_score: int = 5
    chinese_score: int = 6
    business_score: int = 5
    multimodal_score: int = 0
    tool_use_score: int = 5
    json_score: int = 5
    long_context_score: int = 0
    stability_score: int = 7
    privacy_score: int = 5

    context_window: int = 8192
    max_output_tokens: int = 4096
    supports_stream: bool = True
    supports_json_mode: bool = False
    supports_function_calling: bool = False
    supports_vision: bool = False
    supports_audio: bool = False

    cost_relative: float = 1.0
    latency_relative: float = 1.0
    api_base: Optional[str] = None
    api_key_env: Optional[str] = None
    api_protocol: str = "openai_chat_completions"
    region: str = "global"
    fallback_group: str = "general"
    available: bool = False
    last_checked_at: Optional[str] = None
    source: str = "builtin"
    notes: str = ""

    def has_capability(self, capability: str) -> bool:
        return capability in set(self.capabilities)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["provider"] = self.provider.value
        data["model_type"] = self.model_type.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelInfo":
        payload = dict(data)
        if isinstance(payload.get("provider"), str):
            try:
                payload["provider"] = Provider(payload["provider"])
            except ValueError:
                payload["provider"] = Provider.CUSTOM
        if isinstance(payload.get("model_type"), str):
            try:
                payload["model_type"] = ModelType(payload["model_type"])
            except ValueError:
                payload["model_type"] = ModelType.CHAT
        allowed = set(cls.__dataclass_fields__.keys())
        payload = {k: v for k, v in payload.items() if k in allowed}
        return cls(**payload)


@dataclass
class TaskProfile:
    query: str = ""
    category: TaskCategory = TaskCategory.CHAT
    complexity: Complexity = Complexity.LOW
    language: str = "zh"
    expected_output_tokens: int = 1024
    context_estimate: int = 4096

    requires_reasoning: bool = False
    requires_coding: bool = False
    requires_web: bool = False
    requires_vision: bool = False
    requires_audio: bool = False
    requires_long_context: bool = False
    requires_file_access: bool = False
    requires_tool_calling: bool = False
    requires_json_output: bool = False
    requires_image_generation: bool = False
    requires_video_generation: bool = False

    privacy_level: PrivacyLevel = PrivacyLevel.NORMAL
    cost_preference: CostPreference = CostPreference.BALANCED
    latency_preference: LatencyPreference = LatencyPreference.BALANCED
    quality_preference: CostPreference = CostPreference.BALANCED
    hard_constraints: List[str] = field(default_factory=list)
    matched_signals: List[str] = field(default_factory=list)

    @classmethod
    def from_query(
        cls,
        query: str,
        has_image: bool = False,
        needs_code: bool = False,
        has_tools: bool = False,
        **kwargs: Any,
    ) -> "TaskProfile":
        from core.llm.scene_classifier import classify_scene

        return classify_scene(
            query=query,
            has_image=has_image,
            needs_code=needs_code,
            has_tools=has_tools,
            **kwargs,
        )

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["category"] = self.category.value
        data["complexity"] = self.complexity.value
        data["privacy_level"] = self.privacy_level.value
        data["cost_preference"] = self.cost_preference.value
        data["latency_preference"] = self.latency_preference.value
        data["quality_preference"] = self.quality_preference.value
        return data


@dataclass
class RouteDecision:
    model_name: str
    model_label: str
    provider: str
    should_switch: bool
    task_profile: TaskProfile
    explanation: str = ""
    alternatives: List[str] = field(default_factory=list)
    fallback_models: List[str] = field(default_factory=list)
    confidence: float = 0.0
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    estimated_cost_level: str = "unknown"
    estimated_latency_level: str = "unknown"
    requires_tools: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "selected_model": self.model_name,
            "model_label": self.model_label,
            "provider": self.provider,
            "should_switch": self.should_switch,
            "task_type": self.task_profile.category.value,
            "complexity": self.task_profile.complexity.value,
            "confidence": self.confidence,
            "reason": self.explanation,
            "alternatives": self.alternatives,
            "fallback_models": self.fallback_models,
            "score_breakdown": self.score_breakdown,
            "estimated_cost_level": self.estimated_cost_level,
            "estimated_latency_level": self.estimated_latency_level,
            "requires_tools": self.requires_tools,
        }

    def to_text(self) -> str:
        if self.should_switch:
            return f"🔄 切换至 {self.model_label}\n📋 {self.explanation}"
        return f"✓ 保持当前模型 ({self.model_label})"
