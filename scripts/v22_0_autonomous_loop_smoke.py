from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from agent_kernel.autonomous_loop import AutonomousOperationLoop
r=AutonomousOperationLoop(':memory:').tick('整理思路并生成计划',{'context_confidence':.95}); assert r['goal']['goal_id'].startswith('goal_') and r['task_summary']['terminal'] and r['memory_count']>=1; print(json.dumps({'v22_0_autonomous_loop':'pass','task_summary':r['task_summary']},ensure_ascii=False))
