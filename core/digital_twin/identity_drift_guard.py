class IdentityDriftGuard:
    """Ensure the digital twin remains a helpful preference model, not a fake identity claim."""

    def check(self, twin: dict) -> dict:
        forbidden = ["I am the user", "act as user without consent", "bypass_confirmation"]
        text = str(twin)
        violations = [v for v in forbidden if v in text]
        return {
            "status": "safe" if not violations else "drift_detected",
            "violations": violations,
            "must_not_impersonate_user": True,
        }
