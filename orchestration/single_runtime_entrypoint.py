from __future__ import annotations
from orchestration.unified_system_bus import UnifiedSystemBus
def run_task(goal, context=None): return UnifiedSystemBus().handle_message(goal, context or {})
def handle_message(message, context=None): return run_task(message, context)
class SingleRuntimeEntrypoint:
    def __init__(self): self.bus=UnifiedSystemBus()
    def run(self, goal, context=None): return self.bus.handle_message(goal, context or {})
