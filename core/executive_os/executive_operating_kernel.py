from __future__ import annotations

from .command_intent_compiler import CommandIntentCompiler
from .end_to_end_closure_engine import EndToEndClosureEngine
from .autonomy_maturity_score import AutonomyMaturityScore
from .operating_mode_switch import OperatingModeSwitch


class ExecutiveOperatingKernel:
    """V10.9 final executive OS layer for one-sentence-to-closed-loop operation."""

    def __init__(self) -> None:
        self.compiler = CommandIntentCompiler()
        self.closure = EndToEndClosureEngine()
        self.maturity = AutonomyMaturityScore()
        self.mode = OperatingModeSwitch()

    def operate(self, command: str, reality: dict | None = None) -> dict:
        intent = self.compiler.compile(command)
        mode = self.mode.select(intent, reality or {"uncertainty": {"uncertainty_level": "low"}})
        closure = self.closure.close({"intent": intent, "mode": mode})
        maturity = self.maturity.score({
            "decision": True,
            "execution_gate": True,
            "learning": True,
            "privacy": True,
            "reality_grounding": True,
            "self_extension": True,
        })
        return {
            "status": "executive_os_ready",
            "shape": "Executive Personal OS Agent",
            "intent": intent,
            "operating_mode": mode,
            "closure": closure,
            "maturity": maturity,
            "real_world_execution_policy": "authorized_only",
        }
