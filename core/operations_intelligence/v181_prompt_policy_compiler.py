from __future__ import annotations
from .schemas import IntelligenceArtifact, IntelligenceStatus, new_id

class PromptPolicyCompiler:
    """V181: prompt/policy compiler."""
    def compile(self, preferences: list[str], safety_rules: list[str]) -> IntelligenceArtifact:
        policy = {
            "delivery": "one_command_and_package" if any("压缩包" in p or "命令" in p for p in preferences) else "normal",
            "safety": safety_rules + ["high_risk_requires_approval", "no_secret_exfiltration"],
            "style": "direct_actionable",
        }
        return IntelligenceArtifact(new_id("policy"), "prompt_policy", "policy", IntelligenceStatus.READY, 0.93, policy)
