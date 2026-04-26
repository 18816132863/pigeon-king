class CollaborationProtocol:
    """Internal collaboration rules: debate before execution, verify before claim."""

    def apply(self, delegated: dict) -> dict:
        return {
            "status": "protocol_applied",
            "rules": [
                "critic_reviews_before_operator",
                "verifier_checks_before_success_claim",
                "learner_updates_only_after_verified_outcome",
                "no_role_can_bypass_authorization_gateway",
            ],
            "delegated": delegated,
        }
