"""Minimal JSONL telemetry for model routing and calls."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional


def _log_dir() -> Path:
    path = Path.home() / ".openclaw" / "model_router_logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def append_route_log(event: Dict[str, Any]) -> str:
    request_id = event.get("request_id") or str(uuid.uuid4())
    payload = {"request_id": request_id, "time": time.strftime("%Y-%m-%dT%H:%M:%S"), **event}
    path = _log_dir() / "routes.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return request_id


def append_call_log(event: Dict[str, Any]) -> str:
    request_id = event.get("request_id") or str(uuid.uuid4())
    payload = {"request_id": request_id, "time": time.strftime("%Y-%m-%dT%H:%M:%S"), **event}
    path = _log_dir() / "calls.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return request_id
