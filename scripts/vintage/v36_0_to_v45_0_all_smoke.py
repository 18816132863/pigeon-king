import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from core.personal_os_v36_v45.operating_organs import *

c=MissionOutcomeContractEngine().compile('明天早上8点提醒我吃饭，三种方式都要')
assert MissionOutcomeContractEngine().validate(c)['ok']

b=HandoffBus()
t=b.create_ticket('agent_kernel','goal_compiler','compile',{'goal':c.user_goal})
b.accept(t.ticket_id)
b.complete(t.ticket_id,{'contract_id':c.contract_id})
assert b.tickets[t.ticket_id].status=='completed'

l=PersonalPatternLearner()
l.record_episode('提醒流程','partial_success',['modify_alarm_timeout'],'端侧多动作必须串行，不要一点点改')
assert 'route_device_actions_through_global_serial_lane' in l.propose_procedure('reminder','device').preferred_steps

rt=ToolGuardrailRuntime()
assert rt.inspect_input(ToolCallRequest('modify_alarm',{'entityId':'120'},'L2',True,'alarm:120')).action=='route_device_serial'
assert rt.inspect_output(ToolCallRequest('modify_alarm',{},is_device_action=True),{'status':'timeout'})['status']=='timeout_pending_verify'

s=DeviceTransactionSaga()
a1=s.make_action('alarm',{'title':'吃饭提醒','time':'08:00'})
a2=s.make_action('notification',{'title':'吃饭提醒'},[a1.action_id])
order=[]
def exe(a): order.append(a.action_id); return {'status':'success'}
def ver(a,raw): return {'status':'success','verified':True}
rs=s.run([a2,a1],exe,ver)
assert order==[a1.action_id,a2.action_id] and all(r.status=='success' for r in rs)

e=CapabilityGapAutodiscovery()
gaps=e.detect(['calendar_device'],['alarm_device'],'reminder')
assert e.decide(e.candidates_for(gaps[0])[-1]).action=='sandbox_test'

assert ScenarioSimulator().simulate([{'step_id':'s1','action_type':'alarm','is_device_action':True,'risk':'L2'}],{'device_lane_allows_parallel':False}).ok_to_execute

bud=AutonomyBudgetScheduler(AutonomyBudget(max_steps=5,max_device_actions=2,max_high_risk_actions=0,max_memory_writes=1))
assert bud.reserve(steps=1,device_actions=1).allowed
assert not bud.reserve(high_risk_actions=1).allowed

assert ContinuousImprovementEvaluator().evaluate('run1',[{'action_id':'a1','status':'success'}],[{'name':'result_verified','passed':True}]).passed

g=AutonomousOSSupremeGate().check({'six_layer_no_l7':True,'goal_contract_ok':True,'handoff_trace_ok':True,'tool_guardrails_ok':True,'device_saga_serial_ok':True,'capability_extension_sandboxed':True,'scenario_simulation_ok':True,'autonomy_budget_ok':True,'memory_guarded':True,'continuous_evaluation_ok':True,'agent_kernel_layer':'L3','has_l7':False})
assert g['pass'], g
print({'v36_0_to_v45_0_all_smoke':'pass','count':10})
