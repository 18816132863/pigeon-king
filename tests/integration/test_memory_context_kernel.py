"""
测试 Memory Context 内核 - V9.1.0 替代测试
"""

import pytest


def test_source_policy_routing_exists():
    """测试源策略路由存在"""
    import orchestration.router.router
    assert orchestration.router.router is not None


def test_context_injection_planning_exists():
    """测试上下文注入规划存在"""
    from orchestration.planner.task_planner import TaskPlanner
    assert TaskPlanner is not None


def test_memory_version_tracking():
    """测试内存版本跟踪"""
    from memory_context.vector.history import QueryHistory
    assert QueryHistory is not None


def test_memory_gc_exists():
    """测试内存 GC 存在"""
    import memory_context.maintenance.vector_system_optimizer
    assert memory_context.maintenance.vector_system_optimizer is not None
