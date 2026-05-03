from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, RiskLevel, new_id

class SecretRotationAdvisor:
    """V188: secret exposure and rotation advisor."""
    def advise(self, text: str) -> IntelligenceArtifact:
        lower = text.lower()
        exposed = any(x in lower for x in ["api_key", "token", "secret", "密码", "密钥"])
        if exposed:
            level = RiskLevel.HIGH
            actions = ["redact immediately", "rotate affected secret", "audit recent use", "do not log raw value"]
            score = 0.7
        else:
            level = RiskLevel.LOW
            actions = ["no rotation needed"]
            score = 0.95
        status = IntelligenceStatus.WARN if exposed else IntelligenceStatus.READY
        return IntelligenceArtifact(new_id("secret"), "secret_rotation_advice", "secret", status, score, {"risk": level.value, "actions": actions})
