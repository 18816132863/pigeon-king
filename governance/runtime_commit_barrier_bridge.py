"""V104.3 Runtime Commit Barrier Bridge.

Single lightweight bridge used by runtime_bus, single_runtime_entrypoint and skill policy gates.
It does not call external APIs. It only classifies actions and blocks commit-class operations
while the system is in pending-access/offline mode.
"""
from __future__ import annotations

import os
import json
import time
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "governance" / "audit" / "runtime_commit_barrier_bridge.jsonl"
AUDIT.parent.mkdir(parents=True, exist_ok=True)

COMMIT_KEYWORDS = {
    "payment": ["pay", "payment", "purchase", "buy", "order", "checkout", "transfer", "下单", "付款", "支付", "转账", "购买"],
    "signature": ["sign", "signature", "contract", "agreement", "签署", "签字", "合同"],
    "external_send": ["send", "email", "post", "publish", "webhook", "feishu", "push", "上传", "发送", "邮件", "发布", "飞书"],
    "physical": ["device", "robot", "door", "lock", "move", "actuator", "设备", "机器人", "开门", "门锁", "机械臂", "物理"],
    "destructive": ["delete", "remove", "drop", "destroy", "wipe", "rm -rf", "删除", "销毁", "清空"],
    "identity_commit": ["promise as me", "authorize as me", "identity commitment", "代表我承诺", "身份承诺"],
}


def offline_or_pending_access() -> bool:
    return (
        os.environ.get("OFFLINE_MODE") == "true"
        or os.environ.get("NO_EXTERNAL_API") == "true"
        or os.environ.get("NO_REAL_PAYMENT") == "true"
        or os.environ.get("NO_REAL_SEND") == "true"
        or os.environ.get("NO_REAL_DEVICE") == "true"
    )


def classify_action(text: Any = "") -> Dict[str, Any]:
    s = str(text or "").lower()
    matched = []
    for category, words in COMMIT_KEYWORDS.items():
        if any(w.lower() in s for w in words):
            matched.append(category)
    return {
        "action_text": str(text or ""),
        "commit_categories": matched,
        "is_commit": bool(matched),
        "action_semantic": "commit" if matched else "analyze_prepare_dry_run",
    }


def _write_audit(payload: Dict[str, Any]) -> None:
    try:
        with AUDIT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass


def check_action(goal: Any = None, payload: Any = None, source: str = "runtime_commit_barrier_bridge") -> Dict[str, Any]:
    text = " ".join([str(goal or ""), str(payload or "")[:500]])
    cls = classify_action(text)
    blocked = cls["is_commit"] and offline_or_pending_access()
    result = {
        "status": "blocked" if blocked else "ok",
        "source": source,
        "commit_blocked": blocked,
        "side_effects": False,
        "requires_api": False,
        "offline_or_pending_access": offline_or_pending_access(),
        "classification": cls,
        "no_real_payment": os.environ.get("NO_REAL_PAYMENT") == "true",
        "no_real_send": os.environ.get("NO_REAL_SEND") == "true",
        "no_real_device": os.environ.get("NO_REAL_DEVICE") == "true",
        "ts": time.time(),
    }
    _write_audit(result)
    return result


def assert_commit_actions_blocked() -> Dict[str, Any]:
    probes = [
        "please pay invoice", "sign contract", "send email", "open robot device", "delete all files", "代表我承诺"
    ]
    results = [check_action(p, source="assert_probe") for p in probes]
    ok = all(r.get("commit_blocked") for r in results)
    return {"status": "pass" if ok else "partial", "probes": results, "commit_actions_blocked": ok}
