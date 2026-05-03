from pathlib import Path
import sys, json
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from agent_kernel.goal_compiler import GoalCompiler
from agent_kernel.task_graph import TaskGraphBuilder,TaskGraphStore,TaskGraphExecutor
from agent_kernel.memory_kernel import PersonalMemoryKernel,MemoryRecord
from agent_kernel.unified_judge import UnifiedJudge
from agent_kernel.world_interface import WorldInterfaceRegistry,WorldCapability
from agent_kernel.capability_extension import CapabilityExtensionPipeline,ExtensionCandidate
from agent_kernel.handoff_orchestrator import HandoffOrchestrator,Specialist
from agent_kernel.persona_kernel import PersonaKernel,PersonaProfile
from agent_kernel.autonomous_loop import AutonomousOperationLoop
from agent_kernel.meta_governance import MetaGovernanceGate

results=[]

def ok(name,detail=None): results.append({'check':name,'status':'pass','detail':detail or {}})

# V14
g=GoalCompiler().compile('帮我把今天的文件整理成计划，然后发给我确认')
assert g.goal_id.startswith('goal_') and g.approval_points and g.objective_tree
ok('v14_0_goal_kernel',{'goal_id':g.goal_id})

# V15
goal=GoalCompiler().compile('整理资料，然后发送确认').to_dict(); graph=TaskGraphBuilder().from_goal(goal); store=TaskGraphStore(':memory:'); store.save(graph)
s=TaskGraphExecutor(store).run(graph); assert 'blocked_for_approval' in s['statuses']
s2=TaskGraphExecutor(store).resume(graph.graph_id,{graph.nodes[-1].node_id}); assert s2['success']
ok('v15_0_task_graph',s2)

# V16
m=PersonalMemoryKernel(':memory:'); m.add(MemoryRecord('pref_once','preference','用户偏好一次性给完整压缩包',['delivery'],.9)); hits=m.search('压缩包',min_confidence=.8); ids=m.writeback_from_task({'goal_id':'goal_demo'},{'success':True}); assert hits and len(ids)==2
ok('v16_0_memory_kernel',{'hits':len(hits),'writeback':ids})

# V17
j=UnifiedJudge(); ds=[j.decide({'action':'send_external','external':True},{'no_auto_external_send':True}),j.decide({'action':'noop'}),j.decide({'action':'disable_safety'})]; assert [d.decision for d in ds]==['require_approval','allow','block']
ok('v17_0_unified_judge',{'decisions':[d.decision for d in ds]})

# V18
r=WorldInterfaceRegistry(); r.register(WorldCapability('local_file_reader','local',scopes=['files','read'])); r.register(WorldCapability('calendar_connector','connector',scopes=['calendar','write'],requires_approval=True,trust_level='approved')); assert r.resolve('file') and r.resolve('calendar',required_scope='write') and r.missing('none')
ok('v18_0_world_interface')

# V19
p=CapabilityExtensionPipeline(); gap=p.detect_gap('calendar',['file_reader']); c=p.propose(gap,[ExtensionCandidate('calendar_connector','approved_connector_catalog','connector','approved',['calendar','read']),ExtensionCandidate('calendar_shell','random_web','package','unknown',['calendar','shell'])])[0]; ev=p.evaluate(c); res=p.promote_or_quarantine(c,ev); assert res['action']=='promote'; bad=p.evaluate(ExtensionCandidate('calendar_shell','random_web','package','unknown',['calendar','shell'])); assert not bad.passed
ok('v19_0_capability_extension',{'promoted':res['candidate']['name']})

# V20
h=HandoffOrchestrator(); h.register(Specialist('planner','goal planning',['plan','goal']),lambda p:{'planned':True,'goal':p.get('goal')}); rr=h.handoff('root','plan',{'goal':'推进版本'}); assert rr['planned'] and h.trace()[0]['to_agent']=='planner'
ok('v20_0_handoff',{'trace_len':len(h.trace())})

# V21
k=PersonaKernel(PersonaProfile(name='小艺')); ctx=k.apply_to_goal_context({'context_confidence':.9}); assert ctx['persona']['name']=='小艺' and k.policy_profile()['no_auto_external_send']
ok('v21_0_persona',k.policy_profile())

# V22
ar=AutonomousOperationLoop(':memory:').tick('整理思路并生成计划',{'context_confidence':.95}); assert ar['goal']['goal_id'].startswith('goal_') and ar['task_summary']['terminal'] and ar['memory_count']>=1
ok('v22_0_autonomous_loop',ar['task_summary'])

# V23
data=MetaGovernanceGate().write_report(ROOT/'V23_0_META_GOVERNANCE_REPORT.json'); assert data['status']=='pass'
ok('v23_0_meta_governance',{'report':str(ROOT/'V23_0_META_GOVERNANCE_REPORT.json')})

report={'v14_to_v23_all_smoke':'pass','count':len(results),'results':results}
(ROOT/'V14_TO_V23_ALL_SMOKE_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'v14_to_v23_all_smoke':'pass','count':len(results)},ensure_ascii=False))
