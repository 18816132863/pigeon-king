# -*- coding: utf-8 -*-
def test_v85_total_model_module_routes():
    from core.llm import init_model_system, auto_route
    init_model_system()
    cases = [
        ("帮我检查模型决策引擎架构，并一次性修复", {}),
        ("pytest报错帮我修复", {}),
        ("低成本批量生成100条直播话术", {}),
        ("截图报错帮我看一下", {"has_image": True}),
        ("做一个小谷元店铺头像logo", {}),
        ("生成一个30秒真人带货视频", {}),
    ]
    for q, kw in cases:
        r = auto_route(q, **kw)
        assert r.model_name
        assert r.confidence >= 0

def test_v85_provider_guard_no_direct_business_calls():
    from core.llm.provider_guard import scan
    findings = scan()
    assert findings == []
