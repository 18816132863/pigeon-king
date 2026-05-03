"""Bridge entrypoint for V167-V196 operations intelligence layer."""

from core.operations_intelligence import (
    OperationsIntelligenceKernel,
    init_operations_intelligence,
    run_operations_intelligence_cycle,
)

__all__ = ["OperationsIntelligenceKernel", "init_operations_intelligence", "run_operations_intelligence_cycle"]
