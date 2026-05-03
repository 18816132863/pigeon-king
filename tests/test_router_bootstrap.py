"""
测试路由 Bootstrap - V9.1.0 替代测试
skill_entry 模块已移除，使用 orchestration/router 替代
"""

import pytest


def test_router_module_exists():
    """测试路由模块存在"""
    import orchestration.router
    assert orchestration.router is not None


def test_model_router_exists():
    """测试模型路由存在 - V9 新增"""
    from core.llm.model_router import auto_route as ModelRouter  # V85替代旧V5
    assert ModelRouter is not None


def test_skill_router_exists():
    """测试技能路由存在"""
    from orchestration.router.skill_router import SkillRouter
    assert SkillRouter is not None


def test_router_weights_exist():
    """测试路由权重存在"""
    import orchestration.router.weights
    assert orchestration.router.weights is not None


def test_rrf_fusion_exists():
    """测试 RRF 融合存在"""
    from orchestration.router.rrf import reciprocal_rank_fusion
    assert reciprocal_rank_fusion is not None


def test_route_fallback_exists():
    """测试路由降级存在"""
    import orchestration.route_fallback
    assert orchestration.route_fallback is not None
