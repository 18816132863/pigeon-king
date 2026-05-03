"""Execution Layer (L4) - 能力执行网关

六层架构第四层：管理所有设备能力的注册、发现、执行、故障转移。
"""

from __future__ import annotations

# ── 核心执行 ──
from .speculative_decoding import SpeculativeDecoder, DraftModel, TargetModel
from .capabilities.registry import (
    CapabilityRegistry,
    CapabilityInfo,
    CapabilityStatus,
    get_registry,
    register_capability,
)

# ── 搜索引擎 ──
from .search.search import SearchEngine
from .search.dedup import Deduplicator
from .distributed_search import VectorSharder, DistributedSearcher

# ── RAG 引擎 ──
from .rag.rag_optimizer import (
    RAGQueryOptimizer,
    HyDEQueryRewriter,
    SubQueryDecomposer,
    QueryExpander,
    MultiQueryFusion,
)
from .rag.query_rewriter import QueryRewriter, QueryOptimizer

# ── 量化引擎 ──
from .quantization.quantization import (
    FP16Quantizer,
    INT8Quantizer,
    ScalarQuantizer,
    ProductQuantizer,
    BinaryQuantizer,
    create_quantizer,
)
from .quantization.opq_quantization import OPQQuantizer

# ── 向量引擎 ──
from .vector_ops.vector_ops import VectorOps, AVX512VectorOps, get_vector_ops
from .vector_ops.ann import (
    ANNIndex,
    BruteForceANN,
    IVFIndex,
    LSHIndex,
    HNSWIndex,
    create_ann_index,
)

# ── 优化引擎 ──
from .optimizer.auto_tuner import AutoTuner, PerformanceBenchmark, ABTestFramework

# ── 故障转移 ──
from .failover.failover import FailoverManager, Node, HealthChecker, NodeStatus

# ── 设备操作 ──
from .device_dependency_barrier import DeviceDependencyBarrier, ActionState
from .device_receipt_reconciler import DeviceReceiptReconciler, ReconcileResult, reconcile_device_action
from .action_idempotency_guard import IdempotencyGuard, ActionRecord, stable_action_key
from .device_action_timeout_verifier import DeviceActionTimeoutVerifier, TimeoutVerificationResult, DeviceActionState

# ── Visual Operation Agent ──
from .visual_operation_agent import (
    ScreenObserver,
    ActionExecutor,
    VisualPlanner,
    UIGrounding,
)
from .visual_task_executor import VisualTaskExecutor, VisualTaskResult

__all__ = [
    # Core execution
    "SpeculativeDecoder", "DraftModel", "TargetModel",
    "CapabilityRegistry", "CapabilityInfo", "CapabilityStatus",
    "get_registry", "register_capability",
    # Search
    "SearchEngine", "Deduplicator",
    "VectorSharder", "DistributedSearcher",
    # RAG
    "RAGQueryOptimizer", "HyDEQueryRewriter", "SubQueryDecomposer",
    "QueryExpander", "MultiQueryFusion",
    "QueryRewriter", "QueryOptimizer",
    # Quantization
    "FP16Quantizer", "INT8Quantizer", "ScalarQuantizer",
    "ProductQuantizer", "BinaryQuantizer", "OPQQuantizer",
    "create_quantizer",
    # Vector
    "VectorOps", "AVX512VectorOps", "get_vector_ops",
    "ANNIndex", "BruteForceANN", "IVFIndex", "LSHIndex", "HNSWIndex",
    "create_ann_index",
    # Optimization
    "AutoTuner", "PerformanceBenchmark", "ABTestFramework",
    # Failover
    "FailoverManager", "Node", "HealthChecker", "NodeStatus",
    # Device
    "DeviceDependencyBarrier", "ActionState",
    "DeviceReceiptReconciler", "ReconcileResult", "reconcile_device_action",
    "IdempotencyGuard", "ActionRecord", "stable_action_key",
    "DeviceActionTimeoutVerifier", "TimeoutVerificationResult", "DeviceActionState",
    # Visual Agent
    "ScreenObserver", "ActionExecutor", "VisualPlanner", "UIGrounding",
    "VisualTaskExecutor", "VisualTaskResult",
]
