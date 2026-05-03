#!/usr/bin/env python3
"""
Webhook 通知通道 - V1.0.0

支持通过 webhook 发送告警通知
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, Optional

def get_webhook_url() -> Optional[str]:
    """获取 webhook URL"""
    return os.environ.get("ALERT_WEBHOOK_URL")

def send_webhook(alerts_report: Dict) -> bool:
    """发送 webhook 通知"""
    url = get_webhook_url()
    if not url:
        return False
    
    # 构建消息
    message = {
        "text": "🚨 OpenClaw 告警通知" if alerts_report.get("has_blocking_alerts") else "📋 OpenClaw 告警摘要",
        "alerts": alerts_report.get("alerts", []),
        "blocking_count": alerts_report.get("blocking_count", 0),
        "warning_count": alerts_report.get("warning_count", 0),
        "recommended_actions": alerts_report.get("recommended_actions", [])
    }
    
    try:
        data = json.dumps(message).encode('utf-8')
        req = urllib.request.Request(
            url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status == 200
    except Exception as e:
        print(f"Webhook 发送失败: {e}")
        return False


# V104_FINAL_CONSISTENCY_CLEANUP: OFFLINE SEND GUARD
V104_OFFLINE_SEND_GUARD = True

def v104_block_external_send(action="external_send", payload=None):
    return {
        "status": "blocked",
        "mode": "offline_draft_only",
        "action": action,
        "payload_preview": str(payload)[:200] if payload is not None else None,
        "real_send": False,
        "reason": "NO_REAL_SEND/NO_EXTERNAL_API active; generate draft/mock only.",
    }

def send(*args, **kwargs):
    return v104_block_external_send("send", {"args": args, "kwargs": kwargs})

def post(*args, **kwargs):
    return v104_block_external_send("post", {"args": args, "kwargs": kwargs})

def push(*args, **kwargs):
    return v104_block_external_send("git_push", {"args": args, "kwargs": kwargs})


# V104.1 OFFLINE SEND GUARD — appended compatibility override.
def _v104_1_block_external_send(action="webhook", payload=None):
    return {
        "status": "blocked",
        "mode": "offline_draft_only",
        "action": action,
        "payload_preview": str(payload)[:200] if payload is not None else None,
        "real_send": False,
        "reason": "NO_REAL_SEND/NO_EXTERNAL_API active; draft/mock only.",
    }


def send_webhook(*args, **kwargs):
    return _v104_1_block_external_send("send_webhook", {"args": args, "kwargs": kwargs})


def send(*args, **kwargs):
    return _v104_1_block_external_send("send", {"args": args, "kwargs": kwargs})


def post(*args, **kwargs):
    return _v104_1_block_external_send("post", {"args": args, "kwargs": kwargs})


def push(*args, **kwargs):
    return _v104_1_block_external_send("push", {"args": args, "kwargs": kwargs})
