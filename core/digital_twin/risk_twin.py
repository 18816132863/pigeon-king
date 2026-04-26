class RiskTwin:
    def calibrate(self, feedback: list[dict]) -> dict:
        return {
            "low_risk_auto": True,
            "medium_risk_auto_with_audit": True,
            "high_risk_requires_strong_confirmation": True,
            "external_write_requires_confirmation": True,
        }
