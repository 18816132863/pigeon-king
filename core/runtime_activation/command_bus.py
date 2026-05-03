from __future__ import annotations

from pathlib import Path
from .schemas import RuntimeCommand, CommandResult, CommandStatus, new_id, to_dict
from .storage import JsonStore


class CommandBus:
    """V137: unified runtime command bus."""

    def __init__(self, root: str | Path = ".runtime_activation_state"):
        self.root = Path(root)
        self.commands = JsonStore(self.root / "commands.json")
        self.results = JsonStore(self.root / "command_results.json")

    def accept(self, raw_text: str) -> RuntimeCommand:
        intent = "release" if any(x in raw_text for x in ["版本", "覆盖包", "发布", "压缩包"]) else "execute"
        risk = "high" if any(x in raw_text for x in ["发送", "转账", "删除", "安装", "token", "密钥"]) else "normal"
        priority = 90 if "继续" in raw_text or "推进" in raw_text else 50
        cmd = RuntimeCommand(
            id=new_id("cmd"),
            raw_text=raw_text,
            intent=intent,
            priority=priority,
            risk_hint=risk,
        )
        self.commands.append(to_dict(cmd))
        return cmd

    def route(self, command: RuntimeCommand) -> CommandResult:
        if command.risk_hint == "high":
            routed = "core.operating_agent"
            status = CommandStatus.ROUTED
            reason = "high risk command routed to governance layer"
        elif command.intent == "release":
            routed = "core.release_hardening"
            status = CommandStatus.ROUTED
            reason = "release command routed to release hardening layer"
        else:
            routed = "core.operating_spine"
            status = CommandStatus.ROUTED
            reason = "general execution routed to operating spine"
        result = CommandResult(
            id=new_id("cmd_result"),
            command_id=command.id,
            status=status,
            routed_to=routed,
            reason=reason,
            payload={"intent": command.intent, "risk": command.risk_hint},
        )
        self.results.append(to_dict(result))
        return result
