import os
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 最前面，避免被 workspace 级 core 包冲突
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root in sys.path:
    sys.path.remove(_project_root)
sys.path.insert(0, _project_root)
# 如果 sys.modules 里已有 core，清理掉
sys.modules.pop("core", None)
for k in list(sys.modules):
    if k.startswith("core."):
        sys.modules.pop(k, None)

import importlib.util
llm_spec = importlib.util.find_spec("core.llm")
assert llm_spec is not None, f"core.llm spec not found! sys.path={sys.path[:5]}"
assert llm_spec.origin is not None, f"core.llm origin is None! spec={llm_spec}"


def test_v85_architecture_routes_to_reasoner_when_deepseek_available(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-dummy-key-for-testing")
    from core.llm import auto_route

    decision = auto_route("帮我检查模型决策引擎架构，并一次性修复")
    assert decision.task_profile.category.value == "architecture_design"
    # 架构设计任务应路由到推理/高能力模型
    assert decision.model_name in {"gpt-4.1", "deepseek-reasoner", "deepseek-chat", "LLM_ROUTER"}
    assert decision.confidence >= 0


def test_v85_generation_tasks_do_not_use_plain_chat_model():
    from core.llm import auto_route

    video = auto_route("生成一个30秒真人带货视频")
    image = auto_route("做一个小谷元店铺头像logo")
    assert video.task_profile.category.value == "video_generation"
    assert video.model_name == "XIAOYI_VIDEO_TOOL"
    assert image.task_profile.category.value == "image_generation"
    assert image.model_name == "XIAOYI_IMAGE_TOOL"


def test_v85_router_returns_structured_decision():
    from core.llm import auto_route

    decision = auto_route("低成本批量生成100条直播话术")
    data = decision.to_dict()
    assert "selected_model" in data
    assert "fallback_models" in data
    assert "score_breakdown" in data


def test_v85_registry_snapshot_and_report():
    from core.llm import init_model_system, registry

    report = init_model_system()
    assert report["total_models"] >= 10
    assert registry.get_model("LLM_ROUTER") is not None
