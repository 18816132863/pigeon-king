"""V85 decision matrix and scoring functions."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from core.llm.schemas import Complexity, CostPreference, ModelInfo, ModelType, PrivacyLevel, TaskCategory, TaskProfile


CATEGORY_SCORE_FIELD = {
    TaskCategory.CHAT: "chat_score",
    TaskCategory.REWRITE: "chat_score",
    TaskCategory.SUMMARY: "long_context_score",
    TaskCategory.TRANSLATION: "chinese_score",
    TaskCategory.EXTRACTION: "json_score",
    TaskCategory.WRITING: "chinese_score",
    TaskCategory.BUSINESS: "business_score",
    TaskCategory.ECOMMERCE: "business_score",
    TaskCategory.COMPLIANCE: "reasoning_score",
    TaskCategory.ARCHITECTURE: "reasoning_score",
    TaskCategory.CODE: "code_score",
    TaskCategory.DEBUGGING: "code_score",
    TaskCategory.MULTI_FILE_REFACTOR: "code_score",
    TaskCategory.REASONING: "reasoning_score",
    TaskCategory.PLANNING: "reasoning_score",
    TaskCategory.SEARCH: "reasoning_score",
    TaskCategory.DOCUMENT: "long_context_score",
    TaskCategory.DATA: "reasoning_score",
    TaskCategory.VISION: "multimodal_score",
    TaskCategory.IMAGE_GENERATION: "multimodal_score",
    TaskCategory.VIDEO_GENERATION: "multimodal_score",
    TaskCategory.AUDIO: "multimodal_score",
    TaskCategory.DEVICE_CONTROL: "tool_use_score",
    TaskCategory.AGENT: "tool_use_score",
    TaskCategory.AUDIT: "reasoning_score",
}


REQUIRED_CAPABILITIES = {
    "vision": lambda m: m.supports_vision or m.multimodal_score >= 6 or m.model_type == ModelType.VISION,
    "tool_calling": lambda m: m.supports_function_calling or m.tool_use_score >= 7,
    "json": lambda m: m.supports_json_mode or m.json_score >= 7,
    "long_context": lambda m: m.context_window >= 64000 or m.long_context_score >= 7,
    "privacy": lambda m: m.provider.value in {"local", "xiaoyi"} or m.privacy_score >= 7,
}


def model_meets_hard_constraints(model: ModelInfo, task: TaskProfile) -> Tuple[bool, List[str]]:
    missing: List[str] = []
    for constraint in task.hard_constraints:
        checker = REQUIRED_CAPABILITIES.get(constraint)
        if checker and not checker(model):
            missing.append(constraint)
    if task.requires_image_generation and model.model_type != ModelType.IMAGE_GENERATION:
        missing.append("image_generation")
    if task.requires_video_generation and model.model_type != ModelType.VIDEO_GENERATION:
        missing.append("video_generation")
    return not missing, missing


def _norm10(value: float) -> float:
    return max(0.0, min(float(value), 10.0)) / 10.0


def _cost_score(model: ModelInfo, task: TaskProfile) -> float:
    raw = max(0.0, 10.0 - model.cost_relative * 2.0)
    if task.cost_preference == CostPreference.LOW:
        raw = max(0.0, 10.0 - model.cost_relative * 3.5)
    elif task.cost_preference == CostPreference.PREMIUM:
        raw = max(0.0, 10.0 - model.cost_relative * 0.8)
    return _norm10(raw)


def _latency_score(model: ModelInfo, task: TaskProfile) -> float:
    factor = 3.5 if task.latency_preference.value == "realtime" else 2.0
    return _norm10(max(0.0, 10.0 - model.latency_relative * factor))


def _context_score(model: ModelInfo, task: TaskProfile) -> float:
    if model.context_window >= task.context_estimate:
        return 1.0
    ratio = max(model.context_window, 1) / max(task.context_estimate, 1)
    return max(0.0, min(ratio, 1.0))


def score_model(model: ModelInfo, task: TaskProfile, context: Dict[str, Any] | None = None) -> Tuple[float, Dict[str, float]]:
    context = context or {}
    ok, missing = model_meets_hard_constraints(model, task)
    if not ok:
        return -1000.0 - len(missing), {"missing_constraints": float(len(missing))}

    category_field = CATEGORY_SCORE_FIELD.get(task.category, "chat_score")
    primary = _norm10(getattr(model, category_field, model.chat_score))

    capability = primary
    if task.requires_reasoning:
        capability = (capability + _norm10(model.reasoning_score)) / 2
    if task.requires_coding:
        capability = (capability + _norm10(model.code_score)) / 2
    if task.requires_tool_calling:
        capability = (capability + _norm10(model.tool_use_score)) / 2
    if task.requires_json_output:
        capability = (capability + _norm10(model.json_score)) / 2
    if task.language == "zh":
        capability = (capability + _norm10(model.chinese_score)) / 2

    quality = (
        _norm10(model.reasoning_score) * 0.35
        + _norm10(model.code_score) * (0.20 if task.requires_coding else 0.08)
        + _norm10(model.business_score) * (0.18 if task.category in {TaskCategory.BUSINESS, TaskCategory.ECOMMERCE} else 0.05)
        + _norm10(model.chat_score) * 0.12
        + _norm10(model.json_score) * (0.10 if task.requires_json_output else 0.03)
    )
    cost = _cost_score(model, task)
    latency = _latency_score(model, task)
    stability = _norm10(model.stability_score)
    context_score = _context_score(model, task)
    privacy = _norm10(model.privacy_score)

    weights = {
        "capability": 0.35,
        "quality": 0.20,
        "cost": 0.15,
        "latency": 0.10,
        "stability": 0.10,
        "context": 0.05,
        "privacy": 0.05,
    }
    if task.quality_preference == CostPreference.PREMIUM or task.complexity in {Complexity.HIGH, Complexity.VERY_HIGH}:
        weights.update({"capability": 0.38, "quality": 0.27, "cost": 0.07, "latency": 0.06, "stability": 0.12, "context": 0.05, "privacy": 0.05})
    if task.cost_preference == CostPreference.LOW:
        weights.update({"capability": 0.27, "quality": 0.15, "cost": 0.28, "latency": 0.12, "stability": 0.10, "context": 0.04, "privacy": 0.04})
    if task.privacy_level != PrivacyLevel.NORMAL:
        weights.update({"capability": 0.28, "quality": 0.17, "cost": 0.08, "latency": 0.07, "stability": 0.10, "context": 0.05, "privacy": 0.25})

    breakdown = {
        "capability": capability,
        "quality": quality,
        "cost": cost,
        "latency": latency,
        "stability": stability,
        "context": context_score,
        "privacy": privacy,
    }
    total = sum(breakdown[k] * weights[k] for k in weights)

    # Specific bonuses.
    if task.category == TaskCategory.ARCHITECTURE and {"reasoning", "coding"}.issubset(set(model.capabilities)):
        total += 0.05
    if task.category in {TaskCategory.MULTI_FILE_REFACTOR, TaskCategory.DOCUMENT} and model.context_window >= 128000:
        total += 0.04
    if task.category == TaskCategory.ECOMMERCE and model.chinese_score >= 8:
        total += 0.03
    if not model.available:
        total -= 10.0

    return round(total, 6), breakdown


def rank_models(models: Iterable[ModelInfo], task: TaskProfile, context: Dict[str, Any] | None = None) -> List[Tuple[ModelInfo, float, Dict[str, float]]]:
    ranked: List[Tuple[ModelInfo, float, Dict[str, float]]] = []
    for model in models:
        score, breakdown = score_model(model, task, context)
        if score > -100:
            ranked.append((model, score, breakdown))
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked
