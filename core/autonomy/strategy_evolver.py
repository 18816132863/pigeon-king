from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import StrategyRule, QualityReport, new_id, now_ts
from .storage import JsonStore


class StrategyEvolver:
    """V94: strategy evolution based on quality and execution outcomes."""

    def __init__(self, root: str | Path = ".autonomy_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "strategy_rules.json")
        self._ensure_defaults()

    def _ensure_defaults(self) -> None:
        data = self.store.read([])
        if data:
            return
        defaults = [
            StrategyRule(id=new_id("rule"), name="prefer_plan_first", condition="goal_complexity>=medium", action="compile_goal_before_tool_use", weight=1.0),
            StrategyRule(id=new_id("rule"), name="approval_for_external_side_effect", condition="risk>=L3", action="interrupt_for_approval", weight=1.0),
            StrategyRule(id=new_id("rule"), name="write_memory_after_success", condition="quality>=0.75", action="write_episodic_and_procedure_memory", weight=0.8),
        ]
        self.store.write([self._to_dict(x) for x in defaults])

    def evolve_from_quality(self, report: QualityReport) -> List[StrategyRule]:
        data = self.store.read([])
        changed = []
        if report.final_score < 0.75:
            rule = StrategyRule(
                id=new_id("rule"),
                name=f"repair_low_quality::{report.run_id}",
                condition=f"run_id=={report.run_id}",
                action=f"address_issues::{','.join(report.issues) or 'general_quality'}",
                weight=0.6,
            )
            data.append(self._to_dict(rule))
            changed.append(rule)
        else:
            for item in data:
                if item.get("name") == "write_memory_after_success":
                    item["weight"] = min(1.5, float(item.get("weight", 1.0)) + 0.05)
                    item["updated_at"] = now_ts()
                    changed.append(self._from_dict(item))
        self.store.write(data)
        return changed

    def list_rules(self, enabled_only: bool = True) -> List[StrategyRule]:
        rules = [self._from_dict(x) for x in self.store.read([])]
        return [r for r in rules if r.enabled] if enabled_only else rules

    def _to_dict(self, r: StrategyRule) -> Dict:
        return {
            "id": r.id,
            "name": r.name,
            "condition": r.condition,
            "action": r.action,
            "weight": r.weight,
            "enabled": r.enabled,
            "updated_at": r.updated_at,
        }

    def _from_dict(self, item: Dict) -> StrategyRule:
        return StrategyRule(
            id=item["id"],
            name=item["name"],
            condition=item["condition"],
            action=item["action"],
            weight=float(item.get("weight", 1.0)),
            enabled=bool(item.get("enabled", True)),
            updated_at=float(item.get("updated_at", now_ts())),
        )
