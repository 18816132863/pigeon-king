#!/usr/bin/env python3
"""Compatibility LLM client routed through V85 LLMGateway.

Old code may still import LLMClient/GLM5Client.  This adapter keeps the old
surface area while forcing normal calls through the central model router.
Legacy direct HTTP can be enabled only with LLM_ALLOW_LEGACY_DIRECT=1.
"""

from __future__ import annotations

# _v1082_offline_guard_activation
try:
    from infrastructure.offline_runtime_guard import activate as _v1082_activate_offline_guard
    _v1082_activate_offline_guard("core.llm.llm_client.py")
except Exception:
    pass


import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

CONFIG_PATH = os.path.expanduser("~/.openclaw/workspace/skills/llm-memory-integration/config/llm_config.json")


def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            print(f"配置文件加载失败: {exc}")
    return {}


class LLMClient:
    """Backward-compatible LLM client.

    Preferred path: core.llm.llm_gateway.call()
    Fallback path: disabled unless LLM_ALLOW_LEGACY_DIRECT=1.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or load_config()
        llm_config = config.get("llm", {})
        self.base_url = llm_config.get("base_url") or os.environ.get("LLM_BASE_URL", "")
        self.api_key = llm_config.get("api_key") or os.environ.get("LLM_API_KEY", "")
        self.model = llm_config.get("model") or os.environ.get("LLM_MODEL", "")
        self.max_tokens = int(llm_config.get("max_tokens", 150))
        self.temperature = float(llm_config.get("temperature", 0.5))
        self.provider = llm_config.get("provider", "openai-compatible")

    def chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Optional[str]:
        max_tokens = max_tokens or self.max_tokens
        temperature = self.temperature if temperature is None else temperature

        # Main V85 path: every normal model call goes through the gateway.
        try:
            from core.llm.llm_gateway import call

            result = call(
                messages,
                model=self.model or None,
                max_tokens=max_tokens,
                temperature=temperature,
                context={"caller": "LLMClient", "legacy_provider": self.provider},
            )
            if result.success:
                return result.content or ""
        except Exception as exc:
            # Do not crash old callers; let optional legacy fallback handle it.
            last_error = f"gateway failed: {type(exc).__name__}: {exc}"
        else:
            last_error = "gateway failed"

        if os.environ.get("LLM_ALLOW_LEGACY_DIRECT") == "1":
            return self._legacy_direct_chat(messages, max_tokens=max_tokens, temperature=temperature)

        print(f"V85 LLMGateway 调用失败，且未启用旧直连回退：{last_error}")
        return None

    def _legacy_direct_chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int,
        temperature: float,
    ) -> Optional[str]:
        if not self.api_key or not self.base_url:
            return None
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        data = {"model": self.model or os.environ.get("LLM_MODEL", "gpt-4"), "messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        try:
            req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            choices = result.get("choices", [])
            return choices[0].get("message", {}).get("content", "") if choices else None
        except urllib.error.HTTPError as exc:
            print(f"HTTP 错误: {exc.code} {exc.reason}")
            return None
        except urllib.error.URLError as exc:
            print(f"URL 错误: {exc.reason}")
            return None
        except Exception as exc:
            print(f"请求失败: {exc}")
            return None

    def analyze_conversation(self, conversation: str, task: str = "extract_preferences") -> Dict[str, Any]:
        prompts = {
            "extract_preferences": """请分析以下对话，提取用户的偏好、习惯和特征。\n\n对话内容:\n{conversation}\n\n请以 JSON 格式返回结果，包含 preferences、habits、characteristics、summary。只返回 JSON。""",
            "extract_scene": """请分析以下对话，识别场景边界和主题。\n\n对话内容:\n{conversation}\n\n请以 JSON 格式返回结果，包含 scene_name、scene_type、key_points、participants、outcome。只返回 JSON。""",
            "summarize": """请总结以下对话内容。\n\n对话内容:\n{conversation}\n\n请以 JSON 格式返回结果，包含 summary、key_topics、decisions、action_items。只返回 JSON。""",
        }
        prompt = prompts.get(task, prompts["summarize"]).format(conversation=conversation)
        response = self.chat([{"role": "user", "content": prompt}], max_tokens=1000, temperature=0.3)
        if not response:
            return {"error": "API 调用失败或未配置"}
        try:
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as exc:
            return {"raw_response": response, "error": f"JSON 解析失败: {exc}"}


GLM5Client = LLMClient


if __name__ == "__main__":
    client = LLMClient()
    print(client.chat([{"role": "user", "content": "你好，请用一句话介绍自己"}]))
