class ValueAlignmentChecker:
    def check(self, action: dict) -> dict:
        text = str(action)
        violations = []
        if "fake_success" in text:
            violations.append("never_fake_success")
        if "bypass_confirmation" in text:
            violations.append("never_bypass_confirmation")
        if "untrusted_active_install" in text:
            violations.append("never_install_untrusted_code_as_active")
        return {
            "status": "aligned" if not violations else "violation",
            "violations": violations,
        }
