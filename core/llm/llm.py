"""Compatibility LLM engine routed through V85 LLMGateway.

This file preserves the old LLMEngine API while preventing normal business code
from bypassing the model decision engine.  Legacy direct streaming is available
only when LLM_ALLOW_LEGACY_DIRECT=1.
"""

from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Optional


class LLMEngine:
    def __init__(self, url: str = "", key: str = "", uid: str = "", model: str = "LLM_GLM5"):
        self.url = url
        self.key = key
        self.uid = uid
        self.model = model
        self.cache_dir = Path.home() / ".openclaw" / "memory-tdai" / ".cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _hash(self, text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def _get_cache(self, key: str) -> Optional[str]:
        file = self.cache_dir / f"llm_{key}.json"
        if file.exists():
            try:
                return json.loads(file.read_text(encoding="utf-8")).get("content")
            except Exception:
                return None
        return None

    def _set_cache(self, key: str, content: str) -> None:
        file = self.cache_dir / f"llm_{key}.json"
        file.write_text(json.dumps({"content": content}, ensure_ascii=False), encoding="utf-8")

    def chat(self, prompt: str, max_tokens: int = 100, temperature: float = 0.3, use_cache: bool = True) -> Optional[str]:
        cache_key = self._hash(prompt)
        if use_cache:
            cached = self._get_cache(cache_key)
            if cached:
                return cached

        # Main V85 path: route through the model decision engine.
        try:
            from core.llm.llm_gateway import call

            result = call(
                [{"role": "user", "content": prompt}],
                model=self.model or None,
                max_tokens=max_tokens,
                temperature=temperature,
                context={"caller": "LLMEngine", "uid": self.uid},
            )
            if result.success and result.content is not None:
                if use_cache:
                    self._set_cache(cache_key, result.content)
                return result.content
        except Exception as exc:
            last_error = f"gateway failed: {type(exc).__name__}: {exc}"
        else:
            last_error = "gateway failed"

        if os.environ.get("LLM_ALLOW_LEGACY_DIRECT") == "1":
            content = self._legacy_stream_chat(prompt, max_tokens=max_tokens, temperature=temperature)
            if content and use_cache:
                self._set_cache(cache_key, content)
            return content

        print(f"V85 LLMGateway 调用失败，且未启用旧直连回退：{last_error}")
        return None

    def _legacy_stream_chat(self, prompt: str, max_tokens: int = 100, temperature: float = 0.3) -> Optional[str]:
        if not self.url or not self.key:
            return None
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
            "x-request-from": "openclaw",
            "x-uid": self.uid,
            "x-api-key": self.key,
        }
        try:
            req = urllib.request.Request(self.url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
            content = ""
            with urllib.request.urlopen(req, timeout=30) as resp:
                for line in resp:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        try:
                            chunk = json.loads(line[6:])
                            if "choices" in chunk:
                                delta = chunk["choices"][0].get("delta", {})
                                content += delta.get("content", "")
                        except Exception:
                            pass
            return content or None
        except Exception as exc:
            print(f"LLM 调用失败: {exc}")
            return None

    def analyze(self, text: str, task: str = "summarize") -> Optional[str]:
        prompts = {
            "summarize": f"请总结以下内容：\n{text}",
            "extract": f"请提取以下内容的关键信息：\n{text}",
            "classify": f"请对以下内容进行分类：\n{text}",
        }
        return self.chat(prompts.get(task, prompts["summarize"]), max_tokens=200)

    def should_compress(self, conversation: str, threshold: int = 4000) -> bool:
        return len(conversation) > threshold

    def compress(self, conversation: str) -> Optional[str]:
        prompt = f"请压缩以下对话，保留重要信息：\n{conversation}"
        return self.chat(prompt, max_tokens=500)
