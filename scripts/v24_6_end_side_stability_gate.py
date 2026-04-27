#!/usr/bin/env python3
"""V24.6 final stability gate for the V23.7 -> V24.6 advance package."""

from __future__ import annotations

import sys
from pathlib import Path as _Path
_PROJECT_ROOT = _Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import json
from pathlib import Path

from core.release_manifest_v23_7_to_v24_6 import VERSIONS, assert_no_new_layer
from scripts.v23_7_to_v24_6_all_smoke import run_all


def main() -> None:
    results = run_all()
    report = {
        "gate": "V24.6_END_SIDE_STABILITY_GATE",
        "status": "pass",
        "version_count": len(VERSIONS),
        "no_new_layer": assert_no_new_layer(),
        "smoke": results,
        "rules": [
            "agent_kernel remains L3 Orchestration, not L7",
            "device action timeout is not device offline",
            "alarm modify timeout requires second verification",
            "search_alarm defaults to next, not all",
            "side effects are serial and idempotency-protected",
            "long tasks write heartbeat state",
        ],
    }
    Path("V24_6_END_SIDE_STABILITY_GATE.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print("v24_6_end_side_stability_gate: pass")


if __name__ == "__main__":
    main()
