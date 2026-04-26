from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from agent_kernel.goal_compiler import GoalCompiler
from agent_kernel.task_graph import TaskGraphBuilder,TaskGraphStore,TaskGraphExecutor
goal=GoalCompiler().compile('整理资料，然后发送确认').to_dict(); graph=TaskGraphBuilder().from_goal(goal); store=TaskGraphStore(':memory:'); store.save(graph); s=TaskGraphExecutor(store).run(graph); assert 'blocked_for_approval' in s['statuses']; s2=TaskGraphExecutor(store).resume(graph.graph_id,{graph.nodes[-1].node_id}); assert s2['success']; print(json.dumps({'v15_0_task_graph':'pass','summary':s2},ensure_ascii=False))
