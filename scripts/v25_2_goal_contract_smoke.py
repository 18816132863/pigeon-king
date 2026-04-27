#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.goal_contract_v2 import GoalCompilerV2

goal = GoalCompilerV2().compile("明天 8 点用三种方式提醒我吃饭")
assert goal.goal_id.startswith("goal_")
assert "terminal status" in goal.done_definition[0]
assert goal.risk_boundary == "low_risk_auto_allowed"
print("v25_2_goal_contract_smoke: pass")
