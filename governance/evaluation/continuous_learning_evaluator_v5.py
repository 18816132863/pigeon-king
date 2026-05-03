"""V53.0 Continuous Learning Evaluator V5.

Converts completed runs into safe learning suggestions. It never writes long-term
memory directly; it produces candidates for Memory Guard.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List

@dataclass
class LearningSuggestionV5:
    kind: str
    text: str
    confidence: float
    write_target: str

class ContinuousLearningEvaluatorV5:
    def evaluate_run(self, run_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        suggestions: List[LearningSuggestionV5] = []
        if run_summary.get("device_action_timeout_verified"):
            suggestions.append(LearningSuggestionV5(
                kind="procedural",
                text="When a connected device action times out, verify result before retrying and do not mark device offline.",
                confidence=0.86,
                write_target="procedural_memory",
            ))
        if run_summary.get("user_prefers_full_packages"):
            suggestions.append(LearningSuggestionV5(
                kind="preference",
                text="User prefers complete replacement/advance packages with direct commands rather than incremental back-and-forth fixes.",
                confidence=0.82,
                write_target="profile_memory",
            ))
        return [asdict(s) for s in suggestions]
