from __future__ import annotations

from pathlib import Path
from .schemas import ApiRequest, ApiResponse, new_id, to_dict
from .storage import JsonStore


class ApiFacade:
    """V138: internal API facade for runtime activation."""

    def __init__(self, root: str | Path = ".runtime_activation_state"):
        self.root = Path(root)
        self.requests = JsonStore(self.root / "api_requests.json")
        self.responses = JsonStore(self.root / "api_responses.json")

    def handle(self, endpoint: str, method: str = "POST", body: dict | None = None) -> ApiResponse:
        body = body or {}
        req = ApiRequest(id=new_id("api_req"), endpoint=endpoint, method=method.upper(), body=body)
        self.requests.append(to_dict(req))

        if endpoint == "/runtime/activate":
            status = 200
            resp_body = {"accepted": True, "goal": body.get("goal", ""), "mode": "runtime_activation"}
        elif endpoint == "/runtime/status":
            status = 200
            resp_body = {"status": "ok"}
        else:
            status = 404
            resp_body = {"error": "unknown_endpoint"}

        resp = ApiResponse(id=new_id("api_resp"), request_id=req.id, status_code=status, body=resp_body)
        self.responses.append(to_dict(resp))
        return resp
