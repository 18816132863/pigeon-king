#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_kernel.personal_operating_loop_v2 import PersonalOperatingLoopV2

loop = PersonalOperatingLoopV2()
result = loop.plan("明天 8 点用三种方式提醒我吃饭", [
    {"node_id": "alarm", "action": "modify_alarm", "end_side": True},
    {"node_id": "push", "action": "hiboard_push", "end_side": True},
    {"node_id": "cron", "action": "chat_cron", "end_side": False},
])
assert result.status == "planned"
assert result.task_nodes == 3
assert result.end_side_serialized == 2
assert result.memory_writeback_allowed is True
print("v25_7_personal_operating_loop_smoke: pass")
