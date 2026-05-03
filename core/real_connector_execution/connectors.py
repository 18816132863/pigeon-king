from __future__ import annotations

# _v1082_offline_guard_activation
try:
    from infrastructure.offline_runtime_guard import activate as _v1082_activate_offline_guard
    _v1082_activate_offline_guard("real_connector_execution")
except Exception:
    pass


import hashlib
import json
import subprocess
import sys
from execution.unified_tool_execution_gateway import check_tool_call
from pathlib import Path

from .schemas import ConnectorMode, ConnectorStatus, new_id


class BaseConnector:
    def __init__(self, root: str | Path = ".real_connector_execution_state"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def execute(self, binding: dict, mode: ConnectorMode) -> tuple[ConnectorStatus, dict, str]:
        raise NotImplementedError


class FileWorkspaceConnector(BaseConnector):
    def execute(self, binding: dict, mode: ConnectorMode) -> tuple[ConnectorStatus, dict, str]:
        artifacts_dir = self.root / "workspace_artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        body = {
            "binding_id": binding.get("id"),
            "task_id": binding.get("task_id"),
            "task_title": binding.get("task_title"),
            "tool": binding.get("tool_name"),
            "capability": binding.get("capability"),
            "checkpoint_id": binding.get("checkpoint_id"),
        }
        digest = hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:12]
        path = artifacts_dir / f"artifact_{digest}.json"
        path.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
        return ConnectorStatus.EXECUTED, {
            "real_file_written": True,
            "path": str(path),
            "digest": digest,
            "side_effect_scope": "local_workspace_artifact_only",
        }, ""


class MailDraftConnector(BaseConnector):
    def execute(self, binding: dict, mode: ConnectorMode) -> tuple[ConnectorStatus, dict, str]:
        drafts = self.root / "mail_drafts.jsonl"
        draft = {
            "id": new_id("maildraft"),
            "task_title": binding.get("task_title"),
            "subject": "Draft prepared by TopAIOperator",
            "body": f"Prepared draft for: {binding.get('metadata', {}).get('raw_goal', '')}",
            "send_status": "not_sent_requires_approval",
            "checkpoint_id": binding.get("checkpoint_id"),
        }
        with drafts.open("a", encoding="utf-8") as f:
            f.write(json.dumps(draft, ensure_ascii=False) + "\n")
        return ConnectorStatus.DRAFTED, {"draft": draft, "external_send": False}, ""


class CalendarDraftConnector(BaseConnector):
    def execute(self, binding: dict, mode: ConnectorMode) -> tuple[ConnectorStatus, dict, str]:
        drafts = self.root / "calendar_drafts.jsonl"
        draft = {
            "id": new_id("caldraft"),
            "task_title": binding.get("task_title"),
            "operation": "prepare_calendar_action",
            "write_status": "not_written_requires_approval",
            "checkpoint_id": binding.get("checkpoint_id"),
        }
        with drafts.open("a", encoding="utf-8") as f:
            f.write(json.dumps(draft, ensure_ascii=False) + "\n")
        return ConnectorStatus.DRAFTED, {"draft": draft, "external_write": False}, ""


class SafeScriptConnector(BaseConnector):
    ALLOWLIST = [
        [sys.executable, "-V"],
        [sys.executable, "--version"],
    ]

    def execute(self, binding: dict, mode: ConnectorMode) -> tuple[ConnectorStatus, dict, str]:
        if mode != ConnectorMode.REAL:
            return ConnectorStatus.WAITING_APPROVAL, {
                "script_executed": False,
                "reason": "script requires approval unless allowlisted",
                "checkpoint_id": binding.get("checkpoint_id"),
            }, ""
        cmd = [sys.executable, "-V"]
        try:
            gate = check_tool_call(" ".join(cmd), {"source": "SafeScriptConnector"})
            if gate.get("status") == "blocked":
                return ConnectorStatus.BLOCKED, {"script_executed": False, "gateway": gate}, ""
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return ConnectorStatus.EXECUTED, {
                "script_executed": True,
                "cmd": cmd,
                "returncode": res.returncode,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
            }, ""
        except Exception as e:
            return ConnectorStatus.FAILED, {}, repr(e)


class ModelRouteConnector(BaseConnector):
    def execute(self, binding: dict, mode: ConnectorMode) -> tuple[ConnectorStatus, dict, str]:
        # Safe route preparation; no external model call is forced here.
        goal = binding.get("metadata", {}).get("raw_goal", "")
        if any(x in goal for x in ["代码", "debug", "报错"]):
            model_group = "coding_high"
        elif any(x in goal for x in ["图片", "视频", "视觉"]):
            model_group = "multimodal"
        elif any(x in goal for x in ["快", "低成本", "简单"]):
            model_group = "fast_low_cost"
        else:
            model_group = "balanced_reasoning"
        return ConnectorStatus.EXECUTED, {
            "model_route_prepared": True,
            "model_group": model_group,
            "external_call_forced": False,
        }, ""


class ActionBridgeConnector(BaseConnector):
    def execute(self, binding: dict, mode: ConnectorMode) -> tuple[ConnectorStatus, dict, str]:
        return ConnectorStatus.WAITING_APPROVAL, {
            "action_bridge_prepared": True,
            "real_world_side_effect": False,
            "approval_required": True,
            "checkpoint_id": binding.get("checkpoint_id"),
        }, ""


class DevicePrepareConnector(BaseConnector):
    def execute(self, binding: dict, mode: ConnectorMode) -> tuple[ConnectorStatus, dict, str]:
        return ConnectorStatus.WAITING_APPROVAL, {
            "device_action_prepared": True,
            "device_action_executed": False,
            "approval_required": True,
            "checkpoint_id": binding.get("checkpoint_id"),
        }, ""


class GenericConnector(BaseConnector):
    def execute(self, binding: dict, mode: ConnectorMode) -> tuple[ConnectorStatus, dict, str]:
        if mode == ConnectorMode.BLOCKED:
            return ConnectorStatus.BLOCKED, {"blocked": True, "reason": "blocked by policy"}, ""
        if mode == ConnectorMode.APPROVAL_REQUIRED:
            return ConnectorStatus.WAITING_APPROVAL, {"approval_required": True, "tool": binding.get("tool_name")}, ""
        if mode == ConnectorMode.DRY_RUN:
            return ConnectorStatus.PREPARED, {"dry_run": True, "tool": binding.get("tool_name")}, ""
        return ConnectorStatus.EXECUTED, {"executed": True, "safe_internal": True, "tool": binding.get("tool_name")}, ""
