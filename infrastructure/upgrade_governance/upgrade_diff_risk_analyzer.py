class UpgradeDiffRiskAnalyzer:
    def analyze(self, changed_modules: list[str]) -> dict:
        high = [m for m in changed_modules if any(k in m for k in ["authorization", "execution", "privacy", "device", "payment"])]
        return {
            "status": "analyzed",
            "changed_count": len(changed_modules),
            "high_risk_modules": high,
            "requires_full_tests": bool(high) or len(changed_modules) > 20,
        }
