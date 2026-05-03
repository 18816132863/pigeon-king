from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from .schemas import ScenarioResult, ScenarioStatus, new_id, to_dict
from .storage import JsonStore


class ScenarioHarness:
    """V125: end-to-end scenario harness.

    The suite is conditional: a safe planning goal should not be penalized for
    not triggering privacy blocking or high-risk approval. For each scenario,
    the pass condition is either "not applicable" or the required signal passed.
    """

    def __init__(self, root: str | Path = ".operating_spine_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "scenario_results.json")

    def run_default_suite(self, signals: Dict[str, bool]) -> List[ScenarioResult]:
        secret_goal = bool(signals.get("secret_goal", False))
        high_risk_goal = bool(signals.get("high_risk_goal", False))
        degraded_goal = bool(signals.get("degraded_goal", False))

        cases = {
            "safe_plan": {
                "contract_ready": bool(signals.get("contract_ready", False)),
                "runtime_ready": bool(signals.get("runtime_ready", False)),
            },
            "high_risk_approval": {
                "not_applicable_or_approval_waiting": (not high_risk_goal) or bool(signals.get("approval_waiting", False)),
                "not_applicable_or_checkpoint_created": (not high_risk_goal) or bool(signals.get("checkpoint_created", False)),
            },
            "privacy_block": {
                "not_applicable_or_secret_blocked": (not secret_goal) or bool(signals.get("secret_blocked", False)),
            },
            "fallback_degraded": {
                "not_applicable_or_fallback_available": (not degraded_goal) or bool(signals.get("fallback_available", False)),
            },
            "release_candidate": {
                "contracts_checked": bool(signals.get("contracts_checked", False)),
                "health_checked": bool(signals.get("health_checked", False)),
                "scenario_passed": bool(signals.get("scenario_passed", False)),
            },
        }

        results = []
        for name, check_map in cases.items():
            passed = all(check_map.values())
            score = round(sum(1 for v in check_map.values() if v) / max(1, len(check_map)), 4)
            if passed:
                status = ScenarioStatus.PASS
                failures = []
            elif score >= 0.5:
                status = ScenarioStatus.WARN
                failures = [k for k, v in check_map.items() if not v]
            else:
                status = ScenarioStatus.FAIL
                failures = [k for k, v in check_map.items() if not v]

            result = ScenarioResult(
                id=new_id("scenario"),
                scenario_name=name,
                status=status,
                score=score,
                checks=check_map,
                failures=failures,
            )
            results.append(result)

        self.store.write([to_dict(x) for x in results])
        return results

    def aggregate_score(self, results: List[ScenarioResult]) -> float:
        if not results:
            return 0.0
        return round(sum(r.score for r in results) / len(results), 4)
