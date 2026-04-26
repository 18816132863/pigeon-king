#!/usr/bin/env python3
"""
V9 新模块测试
测试 18 个新增模块的基本功能
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestExecutionModules:
    """L4 Execution 层模块测试"""
    
    def test_failover_module_exists(self):
        """测试故障转移模块存在"""
        from execution.failover.failover import FailoverManager
        assert FailoverManager is not None
    
    def test_optimizer_module_exists(self):
        """测试自动调优模块存在"""
        from execution.optimizer.auto_tuner import AutoTuner
        assert AutoTuner is not None
    
    def test_quantization_module_exists(self):
        """测试向量量化模块存在"""
        from execution.quantization.quantization import INT8Quantizer
        assert INT8Quantizer is not None
    
    def test_rag_module_exists(self):
        """测试 RAG 优化模块存在"""
        from execution.rag.rag_optimizer import HyDEQueryRewriter
        assert HyDEQueryRewriter is not None
    
    def test_vector_ops_module_exists(self):
        """测试向量操作模块存在"""
        from execution.vector_ops.vector_ops import VectorOps
        assert VectorOps is not None
    
    def test_speculative_decoding_module_exists(self):
        """测试投机解码模块存在 - V9 正式功能，不允许 skip"""
        from execution.speculative_decoding import SpeculativeDecoder, DraftModel, TargetModel
        assert SpeculativeDecoder is not None
        assert DraftModel is not None
        assert TargetModel is not None
    
    def test_speculative_decoding_functional(self):
        """测试投机解码功能正常工作"""
        import asyncio
        from execution.speculative_decoding import SpeculativeDecoder, DraftModel, TargetModel
        draft = DraftModel()
        target = TargetModel()
        decoder = SpeculativeDecoder(draft, target)
        result = asyncio.run(decoder.decode("test speculative decoding"))
        assert result is not None
        assert hasattr(result, 'tokens')


class TestGovernanceModules:
    """L5 Governance 层模块测试"""
    
    def test_scheduler_module_exists(self):
        """测试实时调度模块存在"""
        from governance.scheduler.realtime_scheduler import RealtimeScheduler
        assert RealtimeScheduler is not None
    
    def test_access_control_module_exists(self):
        """测试访问控制模块存在"""
        from governance.access_control.access_control import AccessControlManager
        assert AccessControlManager is not None
    
    def test_security_module_exists(self):
        """测试安全确认模块存在"""
        from governance.security.security_confirmation import SecurityConfirmation
        assert SecurityConfirmation is not None


class TestInfrastructureModules:
    """L6 Infrastructure 层模块测试"""
    
    def test_vector_engines_module_exists(self):
        """测试三引擎向量架构模块存在"""
        from infrastructure.vector_engines.three_engine_manager import ThreeEngineManager
        assert ThreeEngineManager is not None
    
    def test_cache_module_exists(self):
        """测试缓存优化模块存在"""
        from infrastructure.cache.cache_optimizer import CacheOptimizer
        assert CacheOptimizer is not None
    
    def test_hardware_module_exists(self):
        """测试硬件优化模块存在"""
        from infrastructure.hardware.cpu_optimizer import CPUOptimizer
        assert CPUOptimizer is not None
    
    def test_pool_module_exists(self):
        """测试连接池模块存在"""
        from infrastructure.pool.connection_pool import ConnectionPool
        assert ConnectionPool is not None


class TestOrchestrationModules:
    """L3 Orchestration 层模块测试"""
    
    def test_router_module_exists(self):
        """测试多模型路由模块存在"""
        from orchestration.router.model_router import ModelRouter
        assert ModelRouter is not None
    
    def test_streaming_module_exists(self):
        """测试 LLM 流式输出模块存在"""
        from orchestration.streaming.llm_streaming import LLMStreamer
        assert LLMStreamer is not None
    
    def test_conversation_module_exists(self):
        """测试多轮对话管理模块存在"""
        from orchestration.conversation.conversation import ConversationManager
        assert ConversationManager is not None


class TestMemoryContextModules:
    """L2 Memory Context 层模块测试"""
    
    def test_multimodal_module_exists(self):
        """测试多模态搜索模块存在"""
        from memory_context.multimodal.multimodal_search import MultimodalSearcher
        assert MultimodalSearcher is not None


class TestCoreModules:
    """L1 Core 层模块测试"""
    
    def test_monitoring_module_exists(self):
        """测试性能监控模块存在"""
        from core.monitoring.performance_monitor import PerformanceMonitor
        assert PerformanceMonitor is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
