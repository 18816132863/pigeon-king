from __future__ import annotations

from .preference_versioning import PreferenceVersioning
from .correction_incorporator import CorrectionIncorporator


class IdentityEvolutionEngine:
    """Evolve personal model using corrections while guarding drift."""

    def __init__(self) -> None:
        self.versioning = PreferenceVersioning()
        self.corrections = CorrectionIncorporator()

    def evolve(self, old_model: dict, new_signal: dict) -> dict:
        incorporated = self.corrections.incorporate(old_model, new_signal)
        version = self.versioning.version(old_model, incorporated["model"])
        return {
            "status": "identity_model_evolved",
            "model": incorporated["model"],
            "version": version,
            "safe_to_apply": not version["requires_review"],
        }
