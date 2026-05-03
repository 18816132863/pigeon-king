import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def test_v85_model_engine_fast_routes():
    from core.llm import init_model_system, auto_route
    report = init_model_system()
    assert report["total_models"] >= 10
    assert auto_route("生成一个30秒真人带货视频").model_name == "XIAOYI_VIDEO_TOOL"
    assert auto_route("做一个小谷元店铺头像logo").model_name == "XIAOYI_IMAGE_TOOL"
    assert auto_route("低成本批量生成100条直播话术").task_profile.category.value == "ecommerce_copywriting"
