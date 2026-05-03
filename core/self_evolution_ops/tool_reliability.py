from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional
from .schemas import ReliabilityDecision, CircuitStatus
from .storage import JsonStore


class ToolReliabilityManager:
    """V109: retry budget, circuit breaker and fallback decision."""

    def __init__(self, root: str | Path = ".self_evolution_ops_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "tool_reliability.json")

    def record_result(self, tool_name: str, success: bool) -> None:
        data = self.store.read({})
        item = data.setdefault(tool_name, {"success": 0, "failure": 0})
        if success:
            item["success"] += 1
        else:
            item["failure"] += 1
        self.store.write(data)

    def decide(self, tool_name: str, fallback_tool: Optional[str] = None) -> ReliabilityDecision:
        data = self.store.read({})
        item = data.get(tool_name, {"success": 0, "failure": 0})
        success = int(item.get("success", 0))
        failure = int(item.get("failure", 0))

        if failure >= 5 and failure > success * 2:
            status = CircuitStatus.OPEN
            max_retries = 0
            retry_allowed = False
            reason = "tool circuit opened due to repeated failures"
        elif failure >= 2 and failure >= success:
            status = CircuitStatus.HALF_OPEN
            max_retries = 1
            retry_allowed = True
            reason = "tool is unstable; allow one probe retry"
        else:
            status = CircuitStatus.CLOSED
            max_retries = 2
            retry_allowed = True
            reason = "tool is healthy"

        return ReliabilityDecision(
            tool_name=tool_name,
            circuit_status=status,
            max_retries=max_retries,
            retry_allowed=retry_allowed,
            fallback_tool=fallback_tool,
            reason=reason,
        )
