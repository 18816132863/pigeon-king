from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from agent_kernel.goal_compiler import GoalCompiler
g=GoalCompiler().compile('帮我把今天的文件整理成计划，然后发给我确认')
assert g.goal_id.startswith('goal_') and g.approval_points and g.objective_tree
print(json.dumps({'v14_0_goal_kernel':'pass','goal_id':g.goal_id,'risk':g.risk_boundary},ensure_ascii=False))
