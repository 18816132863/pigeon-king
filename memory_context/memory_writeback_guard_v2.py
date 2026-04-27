"""
V25.4 Memory Writeback Guard V2

Prevents memory pollution. The agent can propose memory; this guard decides whether
the proposal can be stored as semantic / episodic / procedural / preference memory.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


ALLOWED_MEMORY_TYPES = {"semantic", "episodic", "procedural", "preference"}


@dataclass
class MemoryWritebackDecision:
    allowed: bool
    memory_type: str
    reason: str
    sanitized: Dict[str, object]


class MemoryWritebackGuardV2:
    def evaluate(self, proposal: Dict[str, object]) -> MemoryWritebackDecision:
        memory_type = str(proposal.get("memory_type", "episodic"))
        if memory_type not in ALLOWED_MEMORY_TYPES:
            return MemoryWritebackDecision(False, memory_type, "unknown_memory_type", {})

        confidence = float(proposal.get("confidence", 0.0))
        if confidence < 0.65 and memory_type in {"semantic", "preference", "procedural"}:
            return MemoryWritebackDecision(False, memory_type, "low_confidence_for_long_term_memory", {})

        text = str(proposal.get("content", "")).strip()
        if not text:
            return MemoryWritebackDecision(False, memory_type, "empty_content", {})

        sanitized = {
            "memory_type": memory_type,
            "content": text[:2000],
            "source_goal_id": proposal.get("source_goal_id"),
            "confidence": confidence,
            "ttl_policy": proposal.get("ttl_policy", "reviewable"),
        }
        return MemoryWritebackDecision(True, memory_type, "allowed", sanitized)
