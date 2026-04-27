"""V67.0 Evidence-centric execution proof ledger."""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Any
import hashlib, json

@dataclass
class EvidenceRecord:
    evidence_id: str
    action_id: str
    kind: str
    payload_hash: str
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

class EvidenceProofLedger:
    layer = "L6_INFRASTRUCTURE"

    def __init__(self):
        self.records: List[EvidenceRecord] = []

    @staticmethod
    def hash_payload(payload: Dict[str, Any]) -> str:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def add(self, action_id: str, kind: str, payload: Dict[str, Any], metadata=None) -> EvidenceRecord:
        digest = self.hash_payload(payload)
        evidence_id = f"ev_{len(self.records)+1}_{digest[:12]}"
        rec = EvidenceRecord(
            evidence_id=evidence_id,
            action_id=action_id,
            kind=kind,
            payload_hash=digest,
            created_at=datetime.now(timezone.utc).isoformat(),
            metadata=dict(metadata or {}),
        )
        self.records.append(rec)
        return rec

    def proof_chain_for(self, action_id: str) -> List[EvidenceRecord]:
        return [r for r in self.records if r.action_id == action_id]

    def verify_exists(self, action_id: str, required_kind: str) -> bool:
        return any(r.action_id == action_id and r.kind == required_kind for r in self.records)
