from __future__ import annotations
import time, uuid
try:
    from infrastructure.unified_observability_ledger import record_event
    from governance.unified_governance_gate import UnifiedGovernanceGate
except Exception:
    def record_event(*a, **k): return None
    UnifiedGovernanceGate=None
class UnifiedTaskLifecycleEngine:
    def __init__(self): self.gate=UnifiedGovernanceGate() if UnifiedGovernanceGate else None
    def create_task(self,goal,context=None):
        t={'task_id':str(uuid.uuid4()),'goal':goal,'context':context or {},'status':'created','ts':time.time()}; record_event('task_created',t); return t
    def compile_graph(self,task):
        g={'task_id':task['task_id'],'nodes':[{'id':'observe','mode':'dry_run'},{'id':'analyze','mode':'dry_run'},{'id':'prepare','mode':'dry_run'}],'status':'compiled'}; record_event('task_graph_compiled',g); return g
    def schedule(self,graph):
        out={'task_id':graph['task_id'],'status':'scheduled','queue':'inprocess'}; record_event('task_scheduled',out); return out
    def checkpoint(self,task):
        cp={'task_id':task['task_id'],'checkpoint_id':str(uuid.uuid4()),'status':'checkpointed','ts':time.time()}; record_event('task_checkpoint',cp); return cp
    def execute_dry_run(self,task_or_goal,context=None):
        task=task_or_goal if isinstance(task_or_goal,dict) else self.create_task(str(task_or_goal),context); decision=self.gate.check_action(task.get('goal'),task.get('context')).to_dict() if self.gate else {'allowed':True}; graph=self.compile_graph(task); sched=self.schedule(graph); status='blocked' if not decision.get('allowed') else 'completed_dry_run'; out={'task_id':task['task_id'],'status':status,'decision':decision,'graph':graph,'schedule':sched,'checkpoint':self.checkpoint(task),'real_side_effects':0}; record_event('task_executed',out); return out
    def recover(self,task_id,reason):
        out={'task_id':task_id,'status':'recovered','reason':reason,'mode':'local'}; record_event('task_recovered',out); return out
    def complete(self,task_id):
        out={'task_id':task_id,'status':'complete'}; record_event('task_completed',out); return out
def run_task(goal,context=None): return UnifiedTaskLifecycleEngine().execute_dry_run(goal,context)
