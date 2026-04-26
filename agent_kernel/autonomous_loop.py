from .goal_compiler import GoalCompiler
from .task_graph import TaskGraphBuilder,TaskGraphExecutor,TaskGraphStore
from .memory_kernel import PersonalMemoryKernel
from .persona_kernel import PersonaKernel
from .unified_judge import UnifiedJudge
class AutonomousOperationLoop:
    def __init__(self,db=':memory:'):
        self.goal_compiler=GoalCompiler(); self.graph_store=TaskGraphStore(db); self.graph_builder=TaskGraphBuilder(); self.memory=PersonalMemoryKernel(':memory:'); self.persona=PersonaKernel(); self.judge=UnifiedJudge()
    def tick(self,request,context=None,approvals=None):
        context=self.persona.apply_to_goal_context(context or {}); goal=self.goal_compiler.compile(request,context).to_dict()
        action={'action':'execute_goal','mutates_state':True,'external':bool(set(goal.get('information_sources',[]))-{'conversation_context'})}
        decision=self.judge.decide(action,self.persona.policy_profile(),{'context_confidence':context.get('context_confidence',1),'device_state':context.get('device_state','connected')}).to_dict()
        graph=self.graph_builder.from_goal(goal); self.graph_store.save(graph); summary={'skipped':True,'reason':'judge_decision_not_allow'}
        if decision['decision']=='allow' or approvals:
            summary=TaskGraphExecutor(self.graph_store).run(graph,approvals=approvals); self.memory.writeback_from_task(goal,summary)
        return {'goal':goal,'judge_decision':decision,'task_summary':summary,'memory_count':len(self.memory.search())}
