from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from .schemas import PreferenceRule, PreferenceStrength, new_id, to_dict, now_ts
from .storage import JsonStore


class PreferenceRuleEngine:
    """V158: preference rule engine."""

    def __init__(self, root: str | Path = ".personalization_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "preference_rules.json")
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        if self.store.read([]):
            return
        defaults = [
            PreferenceRule(new_id("pref"), "delivery.mode", "package_and_command", PreferenceStrength.HARD, "observed_repeated_request", 0.95, ["delivery"]),
            PreferenceRule(new_id("pref"), "interaction.style", "direct_no_step_by_step", PreferenceStrength.HIGH, "observed_feedback", 0.92, ["style"]),
            PreferenceRule(new_id("pref"), "risk.high_risk", "strong_confirmation", PreferenceStrength.HARD, "explicit_instruction", 0.9, ["safety"]),
            PreferenceRule(new_id("pref"), "artifact.format", "zip_preferred", PreferenceStrength.HIGH, "observed_device_issue", 0.86, ["artifact"]),
        ]
        self.store.write([to_dict(x) for x in defaults])

    def upsert(self, key: str, value: Any, strength: PreferenceStrength, source: str, confidence: float, tags: List[str] | None = None) -> PreferenceRule:
        data = self.store.read([])
        for item in data:
            if item.get("key") == key:
                item.update({"value": value, "strength": strength.value, "source": source, "confidence": confidence, "updated_at": now_ts(), "tags": tags or item.get("tags", [])})
                self.store.write(data)
                return self._from_dict(item)
        rule = PreferenceRule(new_id("pref"), key, value, strength, source, confidence, tags or [])
        data.append(to_dict(rule))
        self.store.write(data)
        return rule

    def match(self, goal: str) -> List[PreferenceRule]:
        rules = [self._from_dict(x) for x in self.store.read([])]
        matched = []
        if any(x in goal for x in ["继续", "推进", "版本", "压缩包", "命令"]):
            matched.extend([r for r in rules if r.key in {"delivery.mode", "interaction.style", "artifact.format"}])
        if any(x in goal for x in ["发送", "删除", "安装", "转账", "客户"]):
            matched.extend([r for r in rules if r.key == "risk.high_risk"])
        # dedupe
        out = []
        seen = set()
        for r in matched:
            if r.key not in seen:
                out.append(r)
                seen.add(r.key)
        return out

    def all(self) -> List[PreferenceRule]:
        return [self._from_dict(x) for x in self.store.read([])]

    def _from_dict(self, item: Dict) -> PreferenceRule:
        return PreferenceRule(
            id=item["id"],
            key=item["key"],
            value=item.get("value"),
            strength=PreferenceStrength(item.get("strength", PreferenceStrength.MEDIUM.value)),
            source=item.get("source", ""),
            confidence=float(item.get("confidence", 0.5)),
            tags=list(item.get("tags", [])),
            updated_at=float(item.get("updated_at", now_ts())),
        )
