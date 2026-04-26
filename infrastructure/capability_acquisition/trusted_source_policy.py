class TrustedSourcePolicy:
    TRUSTED_TYPES = {"builtin", "verified_registry", "local_template", "user_approved"}

    def evaluate_source(self, source_type: str, risk_level: str = "L2") -> dict:
        trusted = source_type in self.TRUSTED_TYPES
        return {
            "trusted": trusted,
            "source_type": source_type,
            "risk_level": risk_level,
            "requires_approval": (not trusted) or risk_level in {"L3", "L4", "BLOCKED"},
            "direct_install_allowed": False,
        }
