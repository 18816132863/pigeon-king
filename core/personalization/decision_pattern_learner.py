from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import DecisionPattern, new_id, to_dict
from .storage import JsonStore


class DecisionPatternLearner:
    """V162: learns recurring decision patterns."""

    def __init__(self, root: str | Path = ".personalization_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "decision_patterns.json")
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if self.store.read([]):
            return
        patterns = [
            DecisionPattern(new_id("pattern"), "version_upgrade", "generate_full_patch_package", "incremental_micro_patch", ["user says don't patch little by little"], 0.9),
            DecisionPattern(new_id("pattern"), "high_risk_action", "dry_run_and_approval", "execute_directly", ["strong confirmation policy"], 0.92),
        ]
        self.store.write([to_dict(p) for p in patterns])

    def infer(self, goal: str) -> DecisionPattern:
        patterns = [self._from_dict(x) for x in self.store.read([])]
        if any(x in goal for x in ["版本", "推进", "压缩包", "命令"]):
            return next((p for p in patterns if p.scenario == "version_upgrade"), patterns[0])
        if any(x in goal for x in ["发送", "删除", "安装", "转账"]):
            return next((p for p in patterns if p.scenario == "high_risk_action"), patterns[0])
        return patterns[0]

    def learn(self, scenario: str, preferred_action: str, avoided_action: str, evidence: List[str], confidence: float = 0.75) -> DecisionPattern:
        data = self.store.read([])
        pattern = DecisionPattern(new_id("pattern"), scenario, preferred_action, avoided_action, evidence, confidence)
        data.append(to_dict(pattern))
        self.store.write(data)
        return pattern

    def _from_dict(self, item: Dict) -> DecisionPattern:
        return DecisionPattern(
            id=item["id"],
            scenario=item["scenario"],
            preferred_action=item["preferred_action"],
            avoided_action=item["avoided_action"],
            evidence=list(item.get("evidence", [])),
            confidence=float(item.get("confidence", 0.5)),
        )
