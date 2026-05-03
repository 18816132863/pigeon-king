"""Unified LLM gateway.

All business code should call this gateway instead of calling vendor SDKs
or hard-coded endpoints directly.  The gateway routes, calls, and falls back.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.llm.model_registry import registry
from core.llm.model_router import route_message
from core.llm.schemas import ModelInfo, Provider
from core.llm.telemetry.model_call_log import append_call_log


@dataclass
class GatewayResult:
    content: Optional[str]
    model_name: str
    provider: str
    success: bool
    error: Optional[str] = None
    fallback_used: bool = False
    route: Optional[Dict[str, Any]] = None
    latency_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model_name": self.model_name,
            "provider": self.provider,
            "success": self.success,
            "error": self.error,
            "fallback_used": self.fallback_used,
            "route": self.route,
            "latency_ms": self.latency_ms,
        }


class LLMGateway:
    def __init__(self, timeout: int = 120):
        self.timeout = timeout

    def call(
        self,
        messages: List[Dict[str, Any]],
        query: Optional[str] = None,
        model: Optional[str] = None,
        has_image: bool = False,
        has_tools: bool = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> GatewayResult:
        user_query = query or self._last_user_text(messages)
        route = route_message(user_query, has_image=has_image, has_tools=has_tools, context=context or {})
        candidates = [model or route.model_name] + [m for m in route.fallback_models if m != (model or route.model_name)]

        last_error: Optional[str] = None
        for index, model_name in enumerate(candidates):
            info = registry.get_model(model_name)
            if not info or not info.available:
                last_error = f"model unavailable: {model_name}"
                continue
            started = time.time()
            try:
                content = self._call_one(info, messages, tools=tools, temperature=temperature, max_tokens=max_tokens, **kwargs)
                latency_ms = int((time.time() - started) * 1000)
                append_call_log({
                    "model": info.name,
                    "provider": info.provider.value,
                    "success": True,
                    "fallback_used": index > 0,
                    "latency_ms": latency_ms,
                    "task_type": route.task_profile.category.value,
                })
                return GatewayResult(content=content, model_name=info.name, provider=info.provider.value, success=True, fallback_used=index > 0, route=route.to_dict(), latency_ms=latency_ms)
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                latency_ms = int((time.time() - started) * 1000)
                append_call_log({
                    "model": info.name,
                    "provider": info.provider.value,
                    "success": False,
                    "fallback_used": index > 0,
                    "latency_ms": latency_ms,
                    "task_type": route.task_profile.category.value,
                    "error": last_error,
                })
                continue

        return GatewayResult(content=None, model_name=candidates[0] if candidates else "", provider="unknown", success=False, error=last_error, fallback_used=len(candidates) > 1, route=route.to_dict())

    def _last_user_text(self, messages: List[Dict[str, Any]]) -> str:
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    return content
                return json.dumps(content, ensure_ascii=False)
        return ""

    def _call_one(
        self,
        model: ModelInfo,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        if model.provider == Provider.XIAOYI:
            raise RuntimeError("XIAOYI provider must be bound by host runtime; no direct HTTP endpoint configured")
        if model.provider == Provider.ANTHROPIC:
            return self._call_anthropic(model, messages, tools, temperature, max_tokens)
        if model.provider == Provider.GEMINI:
            return self._call_gemini(model, messages, temperature, max_tokens)
        return self._call_openai_compatible(model, messages, tools, temperature, max_tokens)

    def _call_openai_compatible(
        self,
        model: ModelInfo,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]],
        temperature: float,
        max_tokens: Optional[int],
    ) -> str:
        api_key_env = model.api_key_env
        api_key = os.environ.get(api_key_env or "")
        if not api_key:
            raise RuntimeError(f"missing api key env: {api_key_env}")
        base = model.api_base or self._default_api_base(model.provider)
        if not base:
            raise RuntimeError(f"missing api_base for provider: {model.provider.value}")
        payload: Dict[str, Any] = {
            "model": model.name,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if tools and model.supports_function_calling:
            payload["tools"] = tools
        if model.supports_json_mode:
            payload.setdefault("response_format", {"type": "json_object"}) if False else None
        req = urllib.request.Request(
            base.rstrip("/") + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("empty choices")
        return choices[0].get("message", {}).get("content", "")

    def _call_anthropic(self, model: ModelInfo, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]], temperature: float, max_tokens: Optional[int]) -> str:
        api_key = os.environ.get(model.api_key_env or "ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("missing api key env: ANTHROPIC_API_KEY")
        system = ""
        converted: List[Dict[str, str]] = []
        for msg in messages:
            if msg.get("role") == "system":
                system += str(msg.get("content", "")) + "\n"
            else:
                converted.append({"role": msg.get("role", "user"), "content": str(msg.get("content", ""))})
        payload: Dict[str, Any] = {"model": model.name, "messages": converted, "max_tokens": max_tokens or model.max_output_tokens, "temperature": temperature}
        if system.strip():
            payload["system"] = system.strip()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-api-key": api_key, "anthropic-version": "2023-06-01"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        parts = data.get("content", [])
        return "".join(part.get("text", "") for part in parts if isinstance(part, dict))

    def _call_gemini(self, model: ModelInfo, messages: List[Dict[str, Any]], temperature: float, max_tokens: Optional[int]) -> str:
        api_key = os.environ.get(model.api_key_env or "GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("missing api key env: GEMINI_API_KEY")
        prompt = "\n".join(f"{m.get('role','user')}: {m.get('content','')}" for m in messages)
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": temperature}}
        if max_tokens:
            payload["generationConfig"]["maxOutputTokens"] = max_tokens
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model.name}:generateContent?key={api_key}"
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("empty candidates")
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(part.get("text", "") for part in parts if isinstance(part, dict))

    def _default_api_base(self, provider: Provider) -> Optional[str]:
        return {
            Provider.OPENAI: "https://api.openai.com/v1",
            Provider.DEEPSEEK: "https://api.deepseek.com",
            Provider.KIMI: "https://api.moonshot.cn/v1",
            Provider.QWEN: "https://dashscope.aliyuncs.com/compatible-mode/v1",
            Provider.ZHIPU: "https://open.bigmodel.cn/api/paas/v4",
            Provider.DOUBAO: "https://ark.cn-beijing.volces.com/api/v3",
        }.get(provider)


def call(messages: List[Dict[str, Any]], **kwargs: Any) -> GatewayResult:
    return LLMGateway().call(messages, **kwargs)
