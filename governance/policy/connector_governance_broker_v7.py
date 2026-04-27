"""V70.0 Connector / MCP-like governance broker."""
from dataclasses import dataclass, field
from typing import Dict, List

@dataclass
class ConnectorRequest:
    connector_id: str
    capability: str
    scopes: List[str] = field(default_factory=list)
    remote: bool = False
    writes_external: bool = False

class ConnectorGovernanceBroker:
    layer = "L5_GOVERNANCE"
    HARD_CONFIRM_SCOPES = {"payment", "delete", "send_external", "export_private", "install_code"}

    def evaluate(self, req: ConnectorRequest) -> Dict[str, str]:
        if any(scope in self.HARD_CONFIRM_SCOPES for scope in req.scopes):
            return {"decision": "confirm", "reason": "hard_confirm_scope"}
        if req.remote and req.writes_external:
            return {"decision": "confirm", "reason": "remote_external_write"}
        if req.remote:
            return {"decision": "allow_with_trace", "reason": "remote_read_or_low_risk"}
        return {"decision": "allow", "reason": "local_low_risk"}
