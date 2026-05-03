from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
import time

from .schemas import PermissionGrant, PermissionScope, new_id, dataclass_to_dict
from .storage import JsonStore


class PermissionVault:
    """V98: scoped permission and approval-token vault."""

    def __init__(self, root: str | Path = ".operating_agent_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "permission_grants.json")

    def grant(self, subject: str, scope: PermissionScope, reason: str, ttl_seconds: Optional[int] = None) -> PermissionGrant:
        data = self.store.read([])
        grant = PermissionGrant(
            id=new_id("perm"),
            subject=subject,
            scope=scope,
            reason=reason,
            expires_at=(time.time() + ttl_seconds) if ttl_seconds else None,
        )
        data.append(dataclass_to_dict(grant))
        self.store.write(data)
        return grant

    def revoke(self, grant_id: str) -> PermissionGrant:
        data = self.store.read([])
        for item in data:
            if item["id"] == grant_id:
                item["revoked"] = True
                self.store.write(data)
                return self._from_dict(item)
        raise KeyError(f"unknown grant_id: {grant_id}")

    def check(self, subject: str, scopes: List[PermissionScope]) -> bool:
        if not scopes:
            return True
        active = self.active(subject)
        have = {g.scope for g in active}
        return set(scopes).issubset(have)

    def active(self, subject: Optional[str] = None) -> List[PermissionGrant]:
        now = time.time()
        grants = []
        for item in self.store.read([]):
            grant = self._from_dict(item)
            if subject and grant.subject != subject:
                continue
            if grant.revoked:
                continue
            if grant.expires_at is not None and grant.expires_at < now:
                continue
            grants.append(grant)
        return grants

    def _from_dict(self, item: Dict) -> PermissionGrant:
        return PermissionGrant(
            id=item["id"],
            subject=item["subject"],
            scope=PermissionScope(item["scope"]),
            reason=item.get("reason", ""),
            expires_at=item.get("expires_at"),
            created_at=float(item.get("created_at", 0.0)),
            revoked=bool(item.get("revoked", False)),
        )
