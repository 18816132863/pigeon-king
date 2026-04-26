#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from infrastructure.connected_adapter_bootstrap import ConnectedAdapterConfig, ConnectedAdapterBootstrap


SAFE_ROUTES = (
    "route.query_note",
    "route.query_alarm",
    "route.query_contact",
    "route.get_location",
    "route.query_message_status",
    "route.list_recent_messages",
)


def load_routes() -> dict:
    path = PROJECT_ROOT / "infrastructure" / "route_registry.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("routes", {})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe-only", action="store_true")
    parser.add_argument("--safe-routes", action="store_true")
    parser.add_argument("--route", default=None)
    args = parser.parse_args()

    probe_only = True if args.probe_only or not args.safe_routes else True
    config = ConnectedAdapterConfig(probe_only=probe_only, runtime_mode="probe_only", safe_routes=SAFE_ROUTES)
    bootstrap = ConnectedAdapterBootstrap(config=config)
    state = bootstrap.bootstrap()

    routes = load_routes()
    selected_routes = [args.route] if args.route else list(SAFE_ROUTES)
    results = []

    for route_id in selected_routes:
        route_meta = routes.get(route_id, {})
        if route_meta.get("risk_level") in {"L3", "L4", "BLOCKED"}:
            results.append({"route_id": route_id, "status": "blocked_by_risk_policy", "side_effect": False})
            continue
        results.append(bootstrap.smoke_route(route_id, state))

    payload = {
        "runtime_mode": "probe_only",
        "adapter_state": state.to_dict(),
        "routes_tested": results,
        "side_effects": False,
        "summary": {
            "total": len(results),
            "ok_or_skipped": sum(1 for r in results if r["status"] in {"ok", "dry_run_ok", "skipped"}),
            "failed": sum(1 for r in results if r["status"] not in {"ok", "dry_run_ok", "skipped"}),
        },
    }

    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_name = "CONNECTED_SMALL_TRAFFIC_REPORT_V9.2.txt" if args.safe_routes else "L0_TIMEOUT_RECOVERY_REPORT_V9.2.txt"
    report_path = reports_dir / report_name
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audit_path = reports_dir / "CONNECTED_ADAPTER_AUDIT_REPORT.txt"
    audit_path.write_text(
        "CONNECTED ADAPTER AUDIT REPORT\n"
        + "=" * 40
        + "\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
