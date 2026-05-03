"""
V26.1 — Universal Task Contract Guard

所有消息进入 TopAIOperatorV26_1 后，必须先生成 UniversalTaskContract
才能调用任何工具。
"""

from .schemas import (
    IntentType,
    SourceContract,
    ActionContract,
    ToolRole,
    ExecutionPolicy,
    RiskLevel,
    StopCondition,
    CompletionCriteria,
    IdempotencyKey,
    UniversalTaskContract,
    ExecutionReport,
    ActionLogEntry,
)
from .contract_builder import ContractBuilder
from .report_generator import ReportGenerator
