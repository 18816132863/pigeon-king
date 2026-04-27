#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from memory_context.memory_writeback_guard_v2 import MemoryWritebackGuardV2

guard = MemoryWritebackGuardV2()
deny = guard.evaluate({"memory_type": "preference", "content": "用户喜欢自动发消息", "confidence": 0.3})
allow = guard.evaluate({"memory_type": "episodic", "content": "modify_alarm 超时后用 search_alarm 二次验证", "confidence": 0.7})
assert deny.allowed is False
assert allow.allowed is True
print("v25_4_memory_writeback_guard_smoke: pass")
