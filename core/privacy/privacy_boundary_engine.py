from __future__ import annotations

from .data_minimization_filter import DataMinimizationFilter
from .scope_redaction_policy import ScopeRedactionPolicy


class PrivacyBoundaryEngine:
    """Prevent personal context leakage when connecting external systems."""

    def __init__(self) -> None:
        self.minimizer = DataMinimizationFilter()
        self.redactor = ScopeRedactionPolicy()

    def prepare_external_payload(self, payload: dict, allowed_keys: list[str]) -> dict:
        minimized = self.minimizer.minimize(payload, allowed_keys)
        redacted = self.redactor.redact(minimized)
        return {
            "status": "privacy_prepared",
            "payload": redacted,
            "minimized": True,
            "redacted": True,
        }
