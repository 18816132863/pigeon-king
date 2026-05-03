"""
V10.1 Preference Evolution Bridge

Bridges PreferenceEvolutionModel into the live personalization pipeline.
- Feeds preference signals from user interactions
- Tracks preference drift and requires review thresholds
- Persists state for cross-session continuity
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import json

from memory_context.preference_evolution_model_v7 import (
    PreferenceEvolutionModel,
    PreferenceSignal,
)


@dataclass
class PreferenceSnapshotMeta:
    snapshot_id: str
    created_at: str
    preference_count: int
    total_confidence: float


class PreferenceEvolutionBridge:
    """Bridge that hooks PreferenceEvolutionModel into user interactions."""

    def __init__(self, storage_dir: str | Path = ".preference_evolution_state"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.model = PreferenceEvolutionModel()
        self.snapshots: List[PreferenceSnapshotMeta] = []
        self._load_latest()

    # ── Ingest signals from user interactions ──────────────────

    def ingest_from_feedback(self, feedback_type: str,
                              feedback_value: Any,
                              confidence_delta: float = 0.15) -> Dict[str, Any]:
        """
        Called when user provides explicit or implicit feedback.
        Examples:
          - "liked this answer" → signal key = "quality_satisfaction"
          - "too verbose" → signal key = "prefer_conciseness"
          - "use dark theme" → signal key = "ui_pref_theme"
        """
        signal = PreferenceSignal(
            key=feedback_type,
            value=feedback_value,
            confidence_delta=confidence_delta,
            source="user_feedback",
            reversible=True,
        )

        proposal = self.model.propose(signal)
        if not proposal["requires_review"]:
            result = self.model.apply(signal)
            proposal["status"] = result

        return proposal

    def ingest_from_procedure(self, procedure_name: str,
                               success: bool,
                               confidence_delta: float = 0.05) -> Dict[str, Any]:
        """Called when a procedure/tool execution succeeds or fails."""
        signal = PreferenceSignal(
            key=f"procedure_{procedure_name}",
            value={"success": success, "last_seen": datetime.now(timezone.utc).isoformat()},
            confidence_delta=confidence_delta,
            source="procedure_success" if success else "procedure_failure",
            reversible=True,
        )

        proposal = self.model.propose(signal)
        if not proposal["requires_review"]:
            result = self.model.apply(signal)
            proposal["status"] = result

        return proposal

    def ingest_from_interaction(self, interaction_key: str,
                                 value: Any,
                                 confidence_delta: float = 0.08) -> Dict[str, Any]:
        """General interaction signal intake."""
        signal = PreferenceSignal(
            key=interaction_key,
            value=value,
            confidence_delta=confidence_delta,
            source="interaction",
            reversible=True,
        )

        proposal = self.model.propose(signal)
        if not proposal["requires_review"]:
            result = self.model.apply(signal)
            proposal["status"] = result

        return proposal

    # ── Query ──────────────────────────────────────────────────

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get current value for a preference key."""
        return self.model.state.values.get(key, default)

    def get_confidence(self, key: str) -> float:
        """Get confidence level for a preference key."""
        return self.model.state.confidence.get(key, 0.0)

    def get_all_preferences(self) -> Dict[str, Dict[str, Any]]:
        """Get all preferences with confidence."""
        result = {}
        for key in self.model.state.values:
            result[key] = {
                "value": self.model.state.values[key],
                "confidence": self.model.state.confidence.get(key, 0.0),
            }
        return result

    # ── Review pipeline ────────────────────────────────────────

    def get_review_candidates(self) -> List[Dict[str, Any]]:
        """Get preferences that need human review (confidence below threshold)."""
        candidates = []
        for key, conf in self.model.state.confidence.items():
            if conf < 0.5 and key in self.model.state.values:
                candidates.append({
                    "key": key,
                    "value": self.model.state.values[key],
                    "confidence": conf,
                })
        return candidates

    # ── Persistence ────────────────────────────────────────────

    def snapshot(self) -> PreferenceSnapshotMeta:
        """Persist current preference state to disk."""
        ts = datetime.now(timezone.utc)
        meta = PreferenceSnapshotMeta(
            snapshot_id=ts.strftime("%Y%m%d_%H%M%S"),
            created_at=ts.isoformat(),
            preference_count=len(self.model.state.values),
            total_confidence=sum(self.model.state.confidence.values()) / max(1, len(self.model.state.confidence)),
        )

        data = {
            "values": self.model.state.values,
            "confidence": self.model.state.confidence,
            "history": [asdict(s) for s in self.model.state.history[-100:]],
            "snapshot_meta": asdict(meta),
        }
        path = self.storage_dir / f"pref_snapshot_{meta.snapshot_id}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

        self.snapshots.append(meta)
        if len(self.snapshots) > 10:
            oldest = self.snapshots.pop(0)
            old_path = self.storage_dir / f"pref_snapshot_{oldest.snapshot_id}.json"
            if old_path.exists():
                old_path.unlink()

        return meta

    def _load_latest(self):
        """Restore latest snapshot on init."""
        snapshots = sorted(self.storage_dir.glob("pref_snapshot_*.json"), reverse=True)
        if not snapshots:
            return
        try:
            data = json.loads(snapshots[0].read_text())
            self.model.state.values = data.get("values", {})
            self.model.state.confidence = data.get("confidence", {})
            for s in data.get("history", []):
                self.model.state.history.append(PreferenceSignal(**s))
        except Exception:
            pass  # Best-effort restore

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "preference_count": len(self.model.state.values),
            "history_length": len(self.model.state.history),
            "avg_confidence": sum(self.model.state.confidence.values()) / max(1, len(self.model.state.confidence)),
            "snapshots": len(self.snapshots),
        }


# Singleton
_PREFERENCE_BRIDGE: Optional[PreferenceEvolutionBridge] = None


def get_preference_evolution_bridge(storage_dir: str = ".preference_evolution_state") -> PreferenceEvolutionBridge:
    global _PREFERENCE_BRIDGE
    if _PREFERENCE_BRIDGE is None:
        _PREFERENCE_BRIDGE = PreferenceEvolutionBridge(storage_dir)
    return _PREFERENCE_BRIDGE
