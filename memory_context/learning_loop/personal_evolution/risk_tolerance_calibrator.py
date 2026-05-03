class RiskToleranceCalibrator:
    def calibrate(self, signals: list[dict]) -> dict:
        prefers_auto = any(s.get("prefer") == "auto" for s in signals)
        return {
            "status": "calibrated",
            "low_risk_auto": True,
            "medium_risk_auto": bool(prefers_auto),
            "high_risk_strong_confirm": True,
        }
