"""V85 model discovery and availability management."""

from __future__ import annotations

# _v1082_offline_guard_activation
try:
    from infrastructure.offline_runtime_guard import activate as _v1082_activate_offline_guard
    _v1082_activate_offline_guard("core.llm.model_discovery.py")
except Exception:
    pass


import json
import re
import os
import re
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

from core.llm.model_registry import registry
from core.llm.schemas import ModelInfo, Provider


PROVIDER_ENV = {
    Provider.OPENAI: "OPENAI_API_KEY",
    Provider.ANTHROPIC: "ANTHROPIC_API_KEY",
    Provider.GEMINI: "GEMINI_API_KEY",
    Provider.DEEPSEEK: "DEEPSEEK_API_KEY",
    Provider.QWEN: "QWEN_API_KEY",
    Provider.KIMI: "MOONSHOT_API_KEY",
    Provider.ZHIPU: "GLM_API_KEY",
    Provider.DOUBAO: "DOUBAO_API_KEY",
    Provider.BAICHUAN: "BAICHUAN_API_KEY",
    Provider.YI: "YI_API_KEY",
    Provider.LOCAL: "LOCAL_LLM_API_KEY",
    Provider.OPENAI_COMPATIBLE: "LLM_API_KEY",
    Provider.CUSTOM: "CUSTOM_API_KEY",
}

CONFIG_FILE_KEY_SOURCES = [
    "~/.openclaw/openclaw.json",
    "~/.openclaw/config.json",
    "~/.openclaw/config.yaml",
    "~/.openclaw/env/deepseek.env",
    "~/.openclaw/workspace/pigeon_king_v10_9/secrets.json",
    "~/.openclaw/workspace/skills/llm-memory-integration/config/llm_config.json",
]

PROVIDER_HINTS = {
    "DEEPSEEK_API_KEY": ["deepseek", "api.deepseek"],
    "OPENAI_API_KEY": ["openai", "api.openai", "gpt-"],
    "ANTHROPIC_API_KEY": ["anthropic", "claude"],
    "GEMINI_API_KEY": ["gemini", "generativelanguage.googleapis"],
    "QWEN_API_KEY": ["qwen", "dashscope", "通义", "千问"],
    "MOONSHOT_API_KEY": ["moonshot", "kimi", "月之暗面"],
    "GLM_API_KEY": ["glm", "zhipu", "bigmodel", "智谱"],
    "DOUBAO_API_KEY": ["doubao", "volces", "ark.cn", "豆包"],
    "BAICHUAN_API_KEY": ["baichuan", "百川"],
    "YI_API_KEY": ["lingyi", "yi-", "零一"],
    "LOCAL_LLM_API_KEY": ["localhost", "127.0.0.1", "ollama", "vllm"],
    "LLM_API_KEY": ["llm_api_key", "openai-compatible", "openai_compatible"],
}


def _config_mentions_provider(text: str, env_var: str) -> bool:
    lowered = text.lower()
    if env_var in text:
        return True
    # Only infer if there is an actual key value (sk-... pattern for standard API keys)
    # PLUS a provider hint. This avoids false positives from config structure keys like
    # "api": "openai-completions" which mention a provider name but don't have a real key.
    has_actual_key = bool(re.search(r'(?:api_key|apikey|api-key|authorization|bearer)\s*[:=]\s*["\']?sk-', lowered, re.IGNORECASE))
    if not has_actual_key:
        return False
    return any(h.lower() in lowered for h in PROVIDER_HINTS.get(env_var, []))


def scan_env_for_keys() -> List[str]:
    active: List[str] = []
    for env_var in set(PROVIDER_ENV.values()):
        if os.environ.get(env_var):
            active.append(env_var)
    for raw in CONFIG_FILE_KEY_SOURCES:
        path = Path(os.path.expanduser(raw))
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for env_var in set(PROVIDER_ENV.values()):
            if env_var not in active and _config_mentions_provider(text, env_var):
                active.append(env_var)
    return sorted(active)


def update_availability() -> List[str]:
    active_keys = set(scan_env_for_keys())
    for model in registry.list_models(available_only=False):
        if model.provider == Provider.XIAOYI:
            model.available = True
            continue
        expected_env = model.api_key_env or PROVIDER_ENV.get(model.provider)
        model.available = bool(expected_env and expected_env in active_keys)
    return sorted(active_keys)


def discover_from_openai_compatible(provider: Provider, api_base: str, api_key_env: str) -> List[ModelInfo]:
    api_key = os.environ.get(api_key_env)
    if not api_key or not api_base:
        return []
    req = urllib.request.Request(
        api_base.rstrip("/") + "/models",
        headers={"Authorization": f"Bearer {api_key}"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []
    items = data.get("data", []) if isinstance(data, dict) else []
    discovered: List[ModelInfo] = []
    for item in items:
        model_id = item.get("id") if isinstance(item, dict) else None
        if not model_id or registry.get_model(model_id):
            continue
        discovered.append(ModelInfo(
            name=model_id,
            provider=provider,
            label=f"{provider.value}:{model_id}",
            api_base=api_base,
            api_key_env=api_key_env,
            available=True,
            source="provider:/models",
            notes="自动发现，能力标签需人工补全",
        ))
    return discovered


def discover_provider_models() -> List[ModelInfo]:
    specs = [
        (Provider.DEEPSEEK, "https://api.deepseek.com", "DEEPSEEK_API_KEY"),
        (Provider.QWEN, "https://dashscope.aliyuncs.com/compatible-mode/v1", "QWEN_API_KEY"),
        (Provider.KIMI, "https://api.moonshot.cn/v1", "MOONSHOT_API_KEY"),
        (Provider.OPENAI, "https://api.openai.com/v1", "OPENAI_API_KEY"),
    ]
    output: List[ModelInfo] = []
    for provider, base, env in specs:
        output.extend(discover_from_openai_compatible(provider, base, env))
    for model in output:
        registry.add_model(model)
    return output


def register_model_external(name: str, label: str, provider: str = "custom", **kwargs: Any) -> bool:
    if registry.get_model(name):
        return False
    model = ModelInfo.from_dict({"name": name, "label": label, "provider": provider, **kwargs})
    registry.add_model(model)
    return True


def generate_availability_report() -> Dict[str, Any]:
    active_keys = update_availability()
    models = registry.list_models(available_only=False)
    available = [m for m in models if m.available]
    unavailable = [m for m in models if not m.available]
    return {
        "total_models": len(models),
        "available": len(available),
        "unavailable": len(unavailable),
        "active_api_keys": active_keys,
        "models": [
            {
                "name": m.name,
                "label": m.label,
                "provider": m.provider.value,
                "available": m.available,
                "fallback_group": m.fallback_group,
                "context_window": m.context_window,
                "best_for": m.best_for,
            }
            for m in models
        ],
    }


def discover_and_register(online_discovery: bool = False) -> Dict[str, Any]:
    update_availability()
    if online_discovery:
        discover_provider_models()
        update_availability()
    registry.save_snapshot()
    return generate_availability_report()
