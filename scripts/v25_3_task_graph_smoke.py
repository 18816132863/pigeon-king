#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orchestration.durable_task_graph_v2 import TaskGraphBuilderV2

graph = TaskGraphBuilderV2().from_goal("goal_demo", [
    {"node_id": "alarm", "action": "modify_alarm", "end_side": True},
    {"node_id": "push", "action": "hiboard_push", "end_side": True},
    {"node_id": "summary", "action": "summarize", "end_side": False},
])
push = [n for n in graph.nodes if n.node_id == "push"][0]
assert "alarm" in push.depends_on
assert len(graph.ready_nodes()) == 2  # alarm and summary
print("v25_3_task_graph_smoke: pass")
