from __future__ import annotations

from .consent_scope_model import ConsentScopeModel
from .action_risk_attestation import ActionRiskAttestation
from .user_confirmation_contract import UserConfirmationContract


class AuthorizationIntentGateway:
    """Gate user intent before any external write/device/connector action."""

    def __init__(self) -> None:
        self.scope = ConsentScopeModel()
        self.attestation = ActionRiskAttestation()
        self.confirmation = UserConfirmationContract()

    def gate(self, action: dict) -> dict:
        scopes = action.get("scopes", [])
        scope = self.scope.evaluate(scopes)
        attestation = self.attestation.attest(action)
        needs_confirm = scope["requires_explicit_consent"] or attestation["requires_confirmation"]
        contract = None
        if needs_confirm:
            contract = self.confirmation.create(
                action.get("action_id", "unknown"),
                attestation["human_readable_summary"],
                attestation["risk_level"],
                scopes,
            )
        return {
            "status": "waiting_confirmation" if needs_confirm else "authorized_for_planning_only",
            "scope": scope,
            "attestation": attestation,
            "confirmation_contract": contract,
            "can_execute_now": False if needs_confirm else not action.get("side_effect", False),
        }
