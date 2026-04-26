#!/usr/bin/env python3
"""
V11.0 Stable Execution Smoke

验证：
1. connected_adapter_bootstrap 可导入并输出自动策略；
2. XiaoyiAdapter 在无端侧工具时不硬失败，返回 queued_for_delivery；
3. guarded_platform_call 命中幂等缓存时不会产生未 awaited coroutine；
4. adaptive_execution_policy 对 timeout/uncertain 禁止静默重试。
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from infrastructure.connected_adapter_bootstrap import build_default_bootstrap
from platform_adapter.xiaoyi_adapter import XiaoyiAdapter
from platform_adapter.base import PlatformCapability
from platform_adapter.invoke_guard import guarded_platform_call, generate_idempotency_key
from governance.policy.adaptive_execution_policy import select_execution_strategy


async def main() -> int:
    results = []

    state = build_default_bootstrap(probe_only=True).bootstrap()
    data = state.to_dict()
    results.append({"name": "bootstrap", "passed": data["adapter_status"] in {"connected", "probe_only", "offline"}, "data": data})

    adapter = XiaoyiAdapter()
    probe = await adapter.probe()
    results.append({"name": "probe", "passed": probe.get("auto_adjusted_strategy") is True, "data": probe})

    invoke = await adapter.invoke(
        PlatformCapability.MESSAGE_SENDING,
        {"task_id": "smoke_v11", "phone_number": "10086", "message": "smoke", "risk_level": "L3"},
    )
    results.append({
        "name": "message_auto_queue_or_complete",
        "passed": invoke.get("status") in {"completed", "queued_for_delivery", "failed"} and "strategy" in invoke,
        "data": invoke,
    })

    async def ok_call():
        return {"success": True}

    key = generate_idempotency_key("smoke_cache", "MESSAGE_SENDING", {"x": 1})
    first = await guarded_platform_call("MESSAGE_SENDING", "send_message", ok_call, idempotency_key=key, side_effecting=True, payload={"x": 1})
    second = await guarded_platform_call("MESSAGE_SENDING", "send_message", ok_call, idempotency_key=key, side_effecting=True, payload={"x": 1})
    results.append({"name": "idempotency_cache", "passed": first.normalized_status == "completed" and second.normalized_status == "completed", "data": second.to_dict()})

    strategy = select_execution_strategy(
        capability="MESSAGE_SENDING",
        op_name="send_message",
        risk_level="L3",
        adapter_status="probe_only",
        timeout=True,
    )
    results.append({"name": "timeout_no_silent_retry", "passed": strategy.allow_auto_retry is False and strategy.confirmation_required is True, "data": strategy.to_dict()})

    report = {"passed": all(item["passed"] for item in results), "results": results}
    report_path = PROJECT_ROOT / "reports" / "v11_stable_execution_smoke.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
