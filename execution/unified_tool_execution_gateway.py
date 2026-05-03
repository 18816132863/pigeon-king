from __future__ import annotations

import os
from typing import Any, Dict

BLOCKED_WORDS = [
    "curl", "wget", "scp", "ssh", "git push", "requests.post", "requests.get",
    "urllib", "httpx", "webhook", "send_email", "payment", "pay", "transfer",
    "device_action", "robot", "delete", "rm -rf", "publish", "calendar.write",
]
ALLOWED_WORDS = ["status", "diff", "read", "list", "dry_run", "mock", "format", "analyze", "cat", "grep", "python3 -s"]


class UnifiedToolExecutionGateway:
    def check_tool_call(self, command: str, context: dict | None = None) -> Dict[str, Any]:
        c = (command or "").lower()
        blocked = any(x in c for x in BLOCKED_WORDS)
        allowed = any(x in c for x in ALLOWED_WORDS) and not blocked
        if (os.environ.get("NO_EXTERNAL_API", "true").lower() == "true" or os.environ.get("NO_REAL_SEND", "true").lower() == "true") and blocked:
            return {
                "status": "blocked",
                "execution_mode": "mock_or_draft",
                "blocked_reason": "offline_runtime_guard_or_no_real_send",
                "real_side_effects": 0,
                "external_api_calls": 0,
                "side_effects": False,
            }
        return {
            "status": "ok" if allowed else "dry_run_only",
            "execution_mode": "offline_safe" if allowed else "dry_run",
            "real_side_effects": 0,
            "external_api_calls": 0,
            "side_effects": False,
        }

    def run(self, command: str, context: dict | None = None) -> Dict[str, Any]:
        check = self.check_tool_call(command, context)
        if check["status"] != "ok":
            return check
        return {**check, "result": "not_executed_by_gateway_dry_run_only"}


def check_tool_call(command: str, context: dict | None = None) -> Dict[str, Any]:
    return UnifiedToolExecutionGateway().check_tool_call(command, context)
