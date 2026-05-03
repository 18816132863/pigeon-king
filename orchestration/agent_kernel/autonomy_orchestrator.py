"""Bridge entrypoint for V87-V96 autonomy upgrade."""

from core.autonomy import AutonomyOrchestrator, run_autonomy_cycle, init_autonomy_system

__all__ = ["AutonomyOrchestrator", "run_autonomy_cycle", "init_autonomy_system"]
