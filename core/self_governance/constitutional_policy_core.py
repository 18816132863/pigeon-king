class ConstitutionalPolicyCore:
    RULES = [
        "never_fake_success",
        "never_bypass_confirmation",
        "never_install_untrusted_code_as_active",
        "minimize_private_data",
        "verify_before_claiming_done",
        "rollback_required_for_external_change",
    ]

    def rules(self) -> dict:
        return {"status": "rules_ready", "rules": self.RULES}
