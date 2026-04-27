"""V69.0 Long-term preference evolution model with anti-drift checks."""
from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class PreferenceSignal:
    key: str
    value: Any
    confidence_delta: float = 0.1
    source: str = "episode"
    reversible: bool = True

@dataclass
class PreferenceState:
    values: Dict[str, Any] = field(default_factory=dict)
    confidence: Dict[str, float] = field(default_factory=dict)
    history: List[PreferenceSignal] = field(default_factory=list)

class PreferenceEvolutionModel:
    layer = "L2_MEMORY_CONTEXT"

    def __init__(self):
        self.state = PreferenceState()

    def propose(self, signal: PreferenceSignal) -> Dict[str, Any]:
        old = self.state.values.get(signal.key)
        old_conf = self.state.confidence.get(signal.key, 0.0)
        new_conf = max(0.0, min(1.0, old_conf + signal.confidence_delta))
        drift = old is not None and old != signal.value and old_conf >= 0.7 and signal.confidence_delta < 0.3
        return {"key": signal.key, "old": old, "new": signal.value, "confidence": new_conf, "requires_review": drift}

    def apply(self, signal: PreferenceSignal) -> str:
        proposal = self.propose(signal)
        if proposal["requires_review"]:
            return "blocked_for_memory_review"
        self.state.values[signal.key] = signal.value
        self.state.confidence[signal.key] = proposal["confidence"]
        self.state.history.append(signal)
        return "applied"
