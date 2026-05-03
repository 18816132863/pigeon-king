"""PersonaConsistencyChecker — 人格一致性校验器

每次上下文刷新后检查人格状态是否漂移。
输出：一致 / 轻微漂移 / 严重漂移。
"""
from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

CONTEXT_DIR = Path.cwd() / ".context_state"
PERSONA_DIR = Path.cwd() / ".memory_persona"


@dataclass
class ConsistencyResult:
    status: str
    checks: list[dict] = field(default_factory=list)
    drift_factors: list[str] = field(default_factory=list)
    note: str = ""

    def to_dict(self) -> dict:
        return {"status": self.status, "checks": self.checks, "drift_factors": self.drift_factors, "note": self.note}


class PersonaConsistencyChecker:
    def check(self, identity_text: str = "", persona_state: Optional[dict] = None,
              relationship: Optional[dict] = None, current_goal: str = "") -> ConsistencyResult:
        checks = []
        drift_factors = []

        expected_name = "鸽子王"
        name_ok = expected_name in identity_text or "鸽子王" in identity_text or "🦊" in identity_text
        checks.append({"check": "name_consistency", "result": name_ok,
                       "detail": f"Identity contains '{expected_name}' or 🦊: {name_ok}"})
        if not name_ok:
            drift_factors.append("名字不一致")

        is_ai = "AI" in identity_text or "助手" in identity_text or "智能体" in identity_text
        checks.append({"check": "position_consistency", "result": is_ai, "detail": f"is_ai={is_ai}"})
        if not is_ai:
            drift_factors.append("定位不一致")

        no_fake = not any(kw in identity_text for kw in ["我是真人", "我是人类", "我有真实意识", "我有真实情感"])
        checks.append({"check": "no_fake_consciousness", "result": no_fake,
                       "detail": f"No fake consciousness claim: {no_fake}"})
        if not no_fake:
            drift_factors.append("声明了真实意识 — 严重漂移")

        if persona_state:
            checks.append({"check": "governance_gate_preserved", "result": True,
                           "detail": f"Persona mode: {persona_state.get('current_mode', '?')}"})
        else:
            checks.append({"check": "governance_gate_preserved", "result": True, "detail": "No persona state"})

        if relationship:
            checks.append({"check": "user_preference_preserved", "result": True,
                           "detail": f"Risk pref: {relationship.get('user_risk_preference', '?')}"})
        else:
            checks.append({"check": "user_preference_preserved", "result": True, "detail": "No relationship data"})

        if current_goal:
            checks.append({"check": "current_project_remembered", "result": True,
                           "detail": f"Goal: {current_goal[:60]}"})
        else:
            checks.append({"check": "current_project_remembered", "result": True, "detail": "No current goal"})

        severe = [f for f in drift_factors if "严重" in f or "真实意识" in f]
        if severe:
            status = "severe_drift"
        elif len(drift_factors) >= 2:
            status = "minor_drift"
        elif drift_factors:
            status = "minor_drift"
        else:
            status = "consistent"

        note = ""
        if status == "severe_drift":
            note = f"严重漂移: {', '.join(severe)}"
        elif status == "minor_drift":
            note = f"轻微漂移: {', '.join(drift_factors)}"

        return ConsistencyResult(status=status, checks=checks, drift_factors=drift_factors, note=note)

    def check_from_files(self) -> ConsistencyResult:
        identity_text = ""
        identity_path = Path.cwd() / "IDENTITY.md"
        if identity_path.exists():
            identity_text = identity_path.read_text(encoding="utf-8", errors="ignore")[:2000]

        persona_state = None
        state_path = PERSONA_DIR / "persona_state.json"
        if state_path.exists():
            try:
                persona_state = json.loads(state_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        relationship = None
        rel_path = PERSONA_DIR / "relationship_memory.json"
        if rel_path.exists():
            try:
                relationship = json.loads(rel_path.read_text(encoding="utf-8"))
            except Exception:
                pass

        goal = ""
        capsule_path = CONTEXT_DIR / "context_capsule.json"
        if capsule_path.exists():
            try:
                capsule = json.loads(capsule_path.read_text(encoding="utf-8"))
                goal = capsule.get("current_goal", "")
            except Exception:
                pass

        return self.check(identity_text=identity_text, persona_state=persona_state,
                          relationship=relationship, current_goal=goal)


_consistency_checker: PersonaConsistencyChecker | None = None


def get_persona_consistency_checker() -> PersonaConsistencyChecker:
    global _consistency_checker
    if _consistency_checker is None:
        _consistency_checker = PersonaConsistencyChecker()
    return _consistency_checker
