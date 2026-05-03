"""V85 model router: message -> task profile -> selected model + fallbacks."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.llm.decision_matrix import rank_models
from core.llm.model_discovery import discover_and_register, register_model_external, update_availability
from core.llm.model_registry import registry
from core.llm.schemas import Complexity, ModelInfo, RouteDecision, TaskCategory, TaskProfile
from core.llm.telemetry.model_call_log import append_route_log


@dataclass
class SwitchHistory:
    max_records: int = 100
    records: List[Dict[str, Any]] = field(default_factory=list)
    current_model: Optional[str] = None

    def record(self, model_name: str, task_profile: TaskProfile, reason: str) -> None:
        self.records.append({
            "model": model_name,
            "task_category": task_profile.category.value,
            "complexity": task_profile.complexity.value,
            "reason": reason,
        })
        if len(self.records) > self.max_records:
            self.records.pop(0)
        self.current_model = model_name

    def get_current(self) -> Optional[str]:
        return self.current_model

    def get_last_switch(self) -> Optional[Dict[str, Any]]:
        return self.records[-1] if self.records else None

    def to_dict(self) -> Dict[str, Any]:
        return {"current_model": self.current_model, "recent_switches": self.records[-10:], "total_switches": len(self.records)}


_switch_history = SwitchHistory()


MODEL_HINTS = {
    "deepseek": "deepseek-chat",
    "deepseek v3": "deepseek-chat",
    "deepseek r1": "deepseek-reasoner",
    "r1": "deepseek-reasoner",
    "gpt-4.1": "gpt-4.1",
    "gpt4.1": "gpt-4.1",
    "gpt-4o": "gpt-4o",
    "gpt4o": "gpt-4o",
    "o3": "o3-mini",
    "o4": "o4-mini",
    "claude": "claude-sonnet-4-20250514",
    "opus": "claude-opus-4",
    "gemini": "gemini-2.5-pro",
    "qwen": "qwen-max",
    "千问": "qwen-max",
    "kimi": "moonshot-v1-128k",
    "月之暗面": "moonshot-v1-128k",
    "glm": "LLM_GLM5",
    "智谱": "LLM_GLM5",
    "豆包": "doubao-pro-128k",
    "本地": "local-openai-compatible",
    "小艺": "LLM_ROUTER",
}


def _explicit_model_from_query(query: str) -> Optional[ModelInfo]:
    q = (query or "").lower()
    for hint, model_name in MODEL_HINTS.items():
        if hint in q:
            model = registry.get_model(model_name)
            if model and model.available:
                return model
    return None


def _cost_level(model: ModelInfo) -> str:
    if model.cost_relative <= 0.3:
        return "low"
    if model.cost_relative <= 1.2:
        return "medium"
    return "high"


def _latency_level(model: ModelInfo) -> str:
    if model.latency_relative <= 0.6:
        return "fast"
    if model.latency_relative <= 1.3:
        return "medium"
    return "slow"


def route_message(
    query: str,
    has_image: bool = False,
    has_tools: bool = False,
    current_model: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    switch_history: Optional[SwitchHistory] = None,
    **classifier_kwargs: Any,
) -> RouteDecision:
    context = context or {}
    update_availability()

    task = TaskProfile.from_query(query=query, has_image=has_image, has_tools=has_tools, **classifier_kwargs)
    explicit_model = _explicit_model_from_query(query)

    ranked = rank_models(registry.list_models(True), task, context)
    if explicit_model:
        selected = explicit_model
        selected_score, selected_breakdown = registry.score(selected, task, context)
    elif ranked:
        selected, selected_score, selected_breakdown = ranked[0]
    else:
        selected = registry.select(task, context)
        selected_score, selected_breakdown = registry.score(selected, task, context)

    fallback_models = [m.name for m, _, _ in ranked if m.name != selected.name][:4]
    alternatives = [m.label for m, _, _ in ranked if m.name != selected.name][:4]
    should_switch = current_model != selected.name
    if current_model is None:
        should_switch = True

    explanation = registry.explain(task, selected)
    confidence = max(0.0, min(1.0, selected_score))
    decision = RouteDecision(
        model_name=selected.name,
        model_label=selected.label,
        provider=selected.provider.value,
        should_switch=should_switch,
        task_profile=task,
        explanation=explanation,
        alternatives=alternatives,
        fallback_models=fallback_models,
        confidence=round(confidence, 3),
        score_breakdown={k: round(v, 4) for k, v in selected_breakdown.items()},
        estimated_cost_level=_cost_level(selected),
        estimated_latency_level=_latency_level(selected),
        requires_tools=task.requires_tool_calling,
    )
    append_route_log(decision.to_dict())
    return decision


def auto_route(query: str, **kwargs: Any) -> RouteDecision:
    decision = route_message(query=query, current_model=_switch_history.get_current(), switch_history=_switch_history, **kwargs)
    if decision.should_switch:
        _switch_history.record(decision.model_name, decision.task_profile, decision.explanation)
    return decision


def get_switch_history() -> SwitchHistory:
    return _switch_history


def init_model_system(online_discovery: bool = False, verbose: bool = False) -> Dict[str, Any]:
    report = discover_and_register(online_discovery=online_discovery)
    if _switch_history.get_current() is None:
        _switch_history.record("LLM_ROUTER", TaskProfile(category=TaskCategory.CHAT, complexity=Complexity.LOW), "系统初始化默认模型")
    if verbose:
        print(f"模型系统初始化完成：已注册 {report['total_models']} 个模型，{report['available']} 个可用")
    return report


__all__ = [
    "SwitchHistory",
    "RouteDecision",
    "route_message",
    "auto_route",
    "get_switch_history",
    "init_model_system",
    "register_model_external",
]
