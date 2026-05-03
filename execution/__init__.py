"""Execution Layer (L4) - lazy facade.

V108.1/V108.2: keep the execution package import-safe under ``python3 -S``.
Heavy execution modules (numpy/pydantic/GPU/vector/visual backends) are loaded only
when their exported symbols are requested. Lightweight gateways may import
``execution`` without waking optional dependencies.
"""
from __future__ import annotations

import importlib
from typing import Any

_EXPORTS = {
    # Core execution
    "SpeculativeDecoder": "execution.speculative_decoding",
    "DraftModel": "execution.speculative_decoding",
    "TargetModel": "execution.speculative_decoding",
    "CapabilityRegistry": "execution.capabilities.registry",
    "CapabilityInfo": "execution.capabilities.registry",
    "CapabilityStatus": "execution.capabilities.registry",
    "get_registry": "execution.capabilities.registry",
    "register_capability": "execution.capabilities.registry",
    # Search
    "SearchEngine": "execution.search.search",
    "Deduplicator": "execution.search.dedup",
    "VectorSharder": "execution.distributed_search",
    "DistributedSearcher": "execution.distributed_search",
    # RAG
    "RAGQueryOptimizer": "execution.rag.rag_optimizer",
    "HyDEQueryRewriter": "execution.rag.rag_optimizer",
    "SubQueryDecomposer": "execution.rag.rag_optimizer",
    "QueryExpander": "execution.rag.rag_optimizer",
    "MultiQueryFusion": "execution.rag.rag_optimizer",
    "QueryRewriter": "execution.rag.query_rewriter",
    "QueryOptimizer": "execution.rag.query_rewriter",
    # Quantization / vector / optimization
    "FP16Quantizer": "execution.quantization.quantization",
    "INT8Quantizer": "execution.quantization.quantization",
    "ScalarQuantizer": "execution.quantization.quantization",
    "ProductQuantizer": "execution.quantization.quantization",
    "BinaryQuantizer": "execution.quantization.quantization",
    "create_quantizer": "execution.quantization.quantization",
    "OPQQuantizer": "execution.quantization.opq_quantization",
    "VectorOps": "execution.vector_ops.vector_ops",
    "AVX512VectorOps": "execution.vector_ops.vector_ops",
    "get_vector_ops": "execution.vector_ops.vector_ops",
    "ANNIndex": "execution.vector_ops.ann",
    "BruteForceANN": "execution.vector_ops.ann",
    "IVFIndex": "execution.vector_ops.ann",
    "LSHIndex": "execution.vector_ops.ann",
    "HNSWIndex": "execution.vector_ops.ann",
    "create_ann_index": "execution.vector_ops.ann",
    "AutoTuner": "execution.optimizer.auto_tuner",
    "PerformanceBenchmark": "execution.optimizer.auto_tuner",
    "ABTestFramework": "execution.optimizer.auto_tuner",
    "FailoverManager": "execution.failover.failover",
    "Node": "execution.failover.failover",
    "HealthChecker": "execution.failover.failover",
    "NodeStatus": "execution.failover.failover",
    # Device / visual
    "DeviceDependencyBarrier": "execution.device_dependency_barrier",
    "ActionState": "execution.device_dependency_barrier",
    "DeviceReceiptReconciler": "execution.device_receipt_reconciler",
    "ReconcileResult": "execution.device_receipt_reconciler",
    "reconcile_device_action": "execution.device_receipt_reconciler",
    "IdempotencyGuard": "execution.action_idempotency_guard",
    "ActionRecord": "execution.action_idempotency_guard",
    "stable_action_key": "execution.action_idempotency_guard",
    "DeviceActionTimeoutVerifier": "execution.device_action_timeout_verifier",
    "TimeoutVerificationResult": "execution.device_action_timeout_verifier",
    "DeviceActionState": "execution.device_action_timeout_verifier",
    "ScreenObserver": "execution.visual_operation_agent",
    "ActionExecutor": "execution.visual_operation_agent",
    "VisualPlanner": "execution.visual_operation_agent",
    "UIGrounding": "execution.visual_operation_agent",
    "VisualTaskExecutor": "execution.visual_task_executor",
    "VisualTaskResult": "execution.visual_task_executor",
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    module_name = _EXPORTS.get(name)
    if not module_name:
        raise AttributeError(name)
    module = importlib.import_module(module_name)
    value = getattr(module, name)
    globals()[name] = value
    return value


def lazy_status() -> dict[str, Any]:
    return {"status": "lazy_facade_active", "exports": len(_EXPORTS), "heavy_modules_preloaded": False}

# V108.1 兼容旧接口名
def optional_status() -> dict[str, Any]:
    return {"lazy_facade": True, "status": "ok", "exports": len(_EXPORTS), "eager_optional_imports": False}
