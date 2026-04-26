#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from infrastructure.connected_adapter_bootstrap import build_default_bootstrap


def main() -> int:
    bootstrap = build_default_bootstrap(probe_only=True)
    state = bootstrap.bootstrap()

    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / "CONNECTED_ADAPTER_BOOTSTRAP_REPORT.txt"

    data = state.to_dict()
    lines = [
        "CONNECTED ADAPTER BOOTSTRAP REPORT",
        "=" * 40,
        f"session_connected: {data['session_connected']}",
        f"runtime_bridge_ready: {data['runtime_bridge_ready']}",
        f"call_device_tool_available: {data['call_device_tool_available']}",
        f"adapter_loaded: {data['adapter_loaded']}",
        f"adapter_status: {data['adapter_status']}",
        f"connected_runtime: {data['connected_runtime']}",
        f"failure_type: {data['failure_type']}",
        f"human_action_required: {data['human_action_required']}",
        f"recovery_steps: {', '.join(data['recovery_steps']) if data['recovery_steps'] else 'none'}",
        "",
        "Raw JSON:",
        json.dumps(data, ensure_ascii=False, indent=2),
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
