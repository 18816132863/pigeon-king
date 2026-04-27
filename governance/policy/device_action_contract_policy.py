"""
V25.0 Device Action Contract Policy

The orchestrator may only send end-side actions to execution when the action contract
has identity, idempotency, timeout and verification rules.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ContractCheck:
    ok: bool
    missing: List[str]
    action_id: str


class DeviceActionContractPolicy:
    required_fields = ("action_id", "idempotency_key", "timeout_profile", "verification_policy")

    def check(self, action: Dict[str, object]) -> ContractCheck:
        missing = [field for field in self.required_fields if not action.get(field)]
        return ContractCheck(ok=not missing, missing=missing, action_id=str(action.get("action_id", "")))
