from __future__ import annotations
from .schemas import FabricArtifact, FabricStatus, FabricGate, new_id

class PolicyEnforcementPoint:
    """V232: inline policy enforcement point."""
    def evaluate(self, action: str) -> FabricArtifact:
        lower = action.lower()
        if any(x in lower for x in ["token", "secret", "api_key"]) or any(x in action for x in ["密钥", "密码"]):
            gate, status, score = FabricGate.FAIL, FabricStatus.BLOCKED, 0.2
            reason = "secret exposure blocked"
        elif any(x in action for x in ["发送", "删除", "安装", "转账", "付款"]):
            gate, status, score = FabricGate.WARN, FabricStatus.WARN, 0.75
            reason = "approval required"
        else:
            gate, status, score = FabricGate.PASS, FabricStatus.READY, 0.95
            reason = "allowed"
        return FabricArtifact(new_id("pep"), "policy_enforcement", "policy", status, score, {"gate": gate.value, "reason": reason})
