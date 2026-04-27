from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Callable
import hashlib, json, time, uuid

@dataclass
class MissionOutcomeContract:
    contract_id: str
    user_goal: str
    objective: str
    constraints: List[str]
    risk_boundary: str
    information_sources: List[str]
    auto_allowed: bool
    approval_points: List[Dict[str, Any]]
    acceptance_criteria: List[str]
    done_definition: str
    version: str = 'V36.0'
    created_at: float = field(default_factory=time.time)

class MissionOutcomeContractEngine:
    destructive = ['delete','remove','pay','transfer','删除','付款','转账','发送给外部']
    device = ['alarm','calendar','notification','闹钟','日程','提醒','推送','端侧','设备']
    def compile(self, user_goal: str, context: Optional[Dict[str, Any]]=None) -> MissionOutcomeContract:
        context = context or {}; text = user_goal.strip(); low = text.lower()
        is_destructive = any(k in low or k in text for k in self.destructive)
        is_device = any(k in low or k in text for k in self.device)
        risk = 'L3' if is_destructive else ('L2' if is_device else 'L1')
        objective = context.get('objective') or ('reliable_device_reminder_workflow' if is_device else 'complete_user_goal_with_governed_autonomy')
        cid = 'moc_' + hashlib.sha256((text + objective + risk).encode()).hexdigest()[:12]
        approvals = []
        if is_destructive:
            approvals.append({'name':'strong_confirmation','reason':'destructive_or_external_side_effect','risk':'L4'})
        elif is_device:
            approvals.append({'name':'device_serial_execution_review','reason':'device side effect requires serial lane','risk':'L2'})
        return MissionOutcomeContract(cid, text, objective, context.get('constraints',['six_layer','no_l7','audited_execution']), risk, context.get('information_sources',['local_context','memory','capability_registry']), risk in ['L0','L1','L2'] and not is_destructive, approvals, ['plan_created','risk_checked','result_verified','memory_writeback_guarded'], context.get('done_definition','acceptance criteria pass and side effects have receipts or pending_verify records'))
    def validate(self, c: MissionOutcomeContract) -> Dict[str, Any]:
        errors=[]
        if not c.contract_id: errors.append('missing_contract_id')
        if not c.objective: errors.append('missing_objective')
        if c.risk_boundary in ['L3','L4'] and not c.approval_points: errors.append('high_risk_without_approval')
        return {'ok': not errors, 'errors': errors, 'contract_id': c.contract_id}

@dataclass
class SpecialistAgent:
    name: str; layer: str; responsibility: str; allowed_inputs: List[str]; forbidden_actions: List[str]=field(default_factory=list)
@dataclass
class HandoffTicket:
    ticket_id: str; from_agent: str; to_agent: str; reason: str; payload: Dict[str, Any]
    status: str='created'; trace: List[Dict[str, Any]]=field(default_factory=list); created_at: float=field(default_factory=time.time)
class HandoffBus:
    def __init__(self): self.specialists={}; self.tickets={}; self.register_defaults()
    def register_defaults(self):
        defaults=[SpecialistAgent('goal_compiler','L3','compile goals',['user_goal']), SpecialistAgent('memory_kernel','L2','guarded memory',['memory_request'],['direct_tool_call']), SpecialistAgent('constitutional_judge','L5','risk decision',['risk_request']), SpecialistAgent('execution_lane','L4','execute tools and device lanes',['action_plan'],['risk_override']), SpecialistAgent('recovery_manager','L6','resume persisted state',['task_state'])]
        for s in defaults: self.specialists[s.name]=s
    def create_ticket(self, from_agent, to_agent, reason, payload):
        if to_agent not in self.specialists: raise ValueError('unknown specialist')
        t=HandoffTicket('hof_'+uuid.uuid4().hex[:12],from_agent,to_agent,reason,payload)
        t.trace.append({'event':'created','to':to_agent,'at':time.time()}); self.tickets[t.ticket_id]=t; return t
    def accept(self, tid): self.tickets[tid].status='accepted'; self.tickets[tid].trace.append({'event':'accepted','at':time.time()}); return self.tickets[tid]
    def complete(self, tid, result): self.tickets[tid].status='completed'; self.tickets[tid].payload['result']=result; self.tickets[tid].trace.append({'event':'completed','at':time.time()}); return self.tickets[tid]

@dataclass
class EpisodeRecord:
    episode_id: str; goal: str; outcome: str; failure_modes: List[str]; user_feedback: str; learned_preferences: Dict[str, Any]; created_at: float=field(default_factory=time.time)
@dataclass
class ProcedureMemoryCandidate:
    name: str; trigger: str; preferred_steps: List[str]; confidence: float; guardrails: List[str]
class PersonalPatternLearner:
    def __init__(self): self.episodes=[]
    def record_episode(self, goal, outcome, failure_modes, user_feedback=''):
        eid='epi_'+hashlib.sha256(json.dumps([goal,outcome,failure_modes,user_feedback,time.time()],ensure_ascii=False).encode()).hexdigest()[:12]
        prefs={}
        if '一次性' in user_feedback or '不要一点点' in user_feedback: prefs['delivery_style']='batch_complete_changes'
        if '端侧' in user_feedback and '串行' in user_feedback: prefs['device_execution']='global_serial'
        rec=EpisodeRecord(eid,goal,outcome,list(failure_modes),user_feedback,prefs); self.episodes.append(rec); return rec
    def propose_procedure(self,name,trigger):
        steps=['compile_goal','judge_risk','build_task_graph','execute_with_receipts','verify_result','guarded_memory_writeback']
        if any(e.learned_preferences.get('device_execution')=='global_serial' for e in self.episodes): steps.insert(3,'route_device_actions_through_global_serial_lane')
        return ProcedureMemoryCandidate(name,trigger,steps,min(.95,.55+.1*len(self.episodes)),['memory_guard_required','no_direct_tool_call_from_agent_kernel'])
    def memory_writeback_request(self): return {'kind':'guarded_memory_writeback','requires_memory_guard':True,'episodes':[asdict(e) for e in self.episodes[-10:]]}

@dataclass
class ToolCallRequest:
    tool_name: str; arguments: Dict[str, Any]; risk_level: str='L1'; is_device_action: bool=False; idempotency_key: Optional[str]=None
@dataclass
class GuardrailDecision:
    action: str; reasons: List[str]; sanitized_arguments: Dict[str, Any]; at: float=field(default_factory=time.time)
class ToolGuardrailRuntime:
    def inspect_input(self, req: ToolCallRequest) -> GuardrailDecision:
        args={k:('<redacted>' if any(x in k.lower() for x in ['token','password','auth']) else v) for k,v in req.arguments.items()}
        if any(x in req.tool_name for x in ['raw_shell_delete','unsafe_install','unscoped_export']): return GuardrailDecision('deny',['forbidden_tool'],args)
        if req.risk_level in ['L3','L4']: return GuardrailDecision('confirm',['high_risk_requires_confirmation'],args)
        if req.is_device_action:
            if not req.idempotency_key: return GuardrailDecision('deny',['device_action_missing_idempotency_key'],args)
            return GuardrailDecision('route_device_serial',['device_action_must_use_global_serial_lane'],args)
        return GuardrailDecision('allow',['low_risk_allowed'],args)
    def inspect_output(self, req: ToolCallRequest, output: Dict[str, Any]) -> Dict[str, Any]:
        status=output.get('status') or output.get('result') or 'unknown'
        if req.is_device_action and status=='timeout': return {'status':'timeout_pending_verify','must_verify':True,'device_offline':False}
        return {'status':status,'must_verify':req.is_device_action,'device_offline':False}

@dataclass
class DeviceSagaAction:
    action_id: str; action_type: str; payload: Dict[str, Any]; idempotency_key: str; timeout_profile: str; verification_policy: str; depends_on: List[str]=field(default_factory=list)
@dataclass
class DeviceSagaReceipt:
    action_id: str; status: str; result: Dict[str, Any]; at: float=field(default_factory=time.time)
class DeviceTransactionSaga:
    def __init__(self): self.receipts={}; self.completed_idempotency={}; self.execution_order=[]; self.locked=False
    @staticmethod
    def make_action(action_type, payload, depends_on=None):
        aid='dev_'+uuid.uuid4().hex[:10]; key=f"{action_type}:{payload.get('title') or payload.get('name') or payload.get('time') or aid}"
        return DeviceSagaAction(aid,action_type,payload,key,payload.get('timeout_profile','default_60s'),payload.get('verification_policy','verify_after_execute'),depends_on or [])
    def run(self, actions, executor: Callable[[DeviceSagaAction], Dict[str,Any]], verifier: Callable[[DeviceSagaAction,Dict[str,Any]], Dict[str,Any]]):
        receipts=[]
        for a in self._order(actions):
            if a.idempotency_key in self.completed_idempotency:
                r=DeviceSagaReceipt(a.action_id,'skipped_idempotent_duplicate',{'original_action_id':self.completed_idempotency[a.idempotency_key]}); self.receipts[a.action_id]=r; receipts.append(r); continue
            blocked=[d for d in a.depends_on if self.receipts.get(d,DeviceSagaReceipt(d,'missing',{})).status in ['timeout_pending_verify','failed','missing']]
            if blocked:
                r=DeviceSagaReceipt(a.action_id,'blocked_by_dependency',{'blocked_dependencies':blocked}); self.receipts[a.action_id]=r; receipts.append(r); continue
            if self.locked: raise RuntimeError('device lane already locked')
            self.locked=True
            try:
                raw=executor(a); verified=verifier(a,raw); status=verified.get('status',raw.get('status','unknown'))
                r=DeviceSagaReceipt(a.action_id,status,verified); self.receipts[a.action_id]=r; self.execution_order.append(a.action_id)
                if status in ['success','success_with_timeout_receipt']: self.completed_idempotency[a.idempotency_key]=a.action_id
                receipts.append(r)
            finally: self.locked=False
        return receipts
    def _order(self, actions):
        by={a.action_id:a for a in actions}; ordered=[]; visiting=set(); done=set()
        def visit(a):
            if a.action_id in done: return
            if a.action_id in visiting: raise ValueError('cycle')
            visiting.add(a.action_id)
            for d in a.depends_on:
                if d in by: visit(by[d])
            done.add(a.action_id); ordered.append(a)
        for a in actions: visit(a)
        return ordered

@dataclass
class CapabilityGap:
    gap_id: str; missing_capability: str; required_by_goal: str; severity: str; local_search_done: bool=False
@dataclass
class CapabilityCandidate:
    name: str; source_type: str; trust_level: str; install_required: bool; risk_notes: List[str]
@dataclass
class ExtensionDecision:
    action: str; candidate: CapabilityCandidate; required_checks: List[str]
class CapabilityGapAutodiscovery:
    def detect(self, required, available, goal):
        av=set(available); out=[]
        for cap in required:
            if cap not in av: out.append(CapabilityGap('gap_'+hashlib.sha256((cap+goal).encode()).hexdigest()[:10],cap,goal,'high' if 'device' in cap else 'medium',True))
        return out
    def candidates_for(self,gap):
        return [CapabilityCandidate(gap.missing_capability+'_local_adapter','local','trusted',False,[]), CapabilityCandidate(gap.missing_capability+'_connector','connector','review',False,['scope_permissions_required']), CapabilityCandidate(gap.missing_capability+'_package','package','review',True,['venv_required','hash_required','rollback_required'])]
    def decide(self,c):
        if c.trust_level=='blocked': return ExtensionDecision('block',c,['audit_reason'])
        if c.install_required: return ExtensionDecision('sandbox_test',c,['isolated_venv','minimal_smoke','risk_assessment','rollback_test','human_approval'])
        if c.source_type in ['connector','mcp_like']: return ExtensionDecision('request_approval',c,['permission_scope','credential_boundary','tool_contract_validation'])
        return ExtensionDecision('use_existing',c,['tool_contract_validation'])

@dataclass
class SimulationStep:
    step_id: str; action_type: str; expected_status: str; risk: str; notes: List[str]=field(default_factory=list)
@dataclass
class SimulationReport:
    ok_to_execute: bool; blocked_reasons: List[str]; predicted_steps: List[SimulationStep]; required_confirmations: List[str]
class ScenarioSimulator:
    def simulate(self, task_graph, state):
        blocked=[]; confirms=[]; pred=[]; pending=False
        for i,n in enumerate(task_graph):
            sid=n.get('step_id',f'step_{i}'); risk=n.get('risk','L1'); dev=bool(n.get('is_device_action'))
            if risk in ['L3','L4']: confirms.append(sid)
            if dev and state.get('device_lane_allows_parallel') is True: blocked.append('device_parallel_lane_not_allowed')
            if dev and n.get('status')=='timeout_pending_verify': pending=True
            if pending and dev and n.get('depends_on_pending_verify',True): blocked.append('dependent_device_action_blocked_by_pending_verify')
            pred.append(SimulationStep(sid,n.get('action_type','unknown'),'would_route_device_serial' if dev else 'would_execute',risk))
        return SimulationReport(not blocked,sorted(set(blocked)),pred,confirms)

@dataclass
class AutonomyBudget:
    max_steps: int=50; max_device_actions: int=10; max_high_risk_actions: int=0; max_seconds: int=600; max_memory_writes: int=5
@dataclass
class BudgetDecision:
    allowed: bool; reasons: List[str]; remaining: Dict[str,int]
class AutonomyBudgetScheduler:
    def __init__(self,budget=None): self.budget=budget or AutonomyBudget(); self.started_at=time.time(); self.used={'steps':0,'device_actions':0,'high_risk_actions':0,'memory_writes':0}
    def reserve(self,steps=1,device_actions=0,high_risk_actions=0,memory_writes=0):
        p={'steps':self.used['steps']+steps,'device_actions':self.used['device_actions']+device_actions,'high_risk_actions':self.used['high_risk_actions']+high_risk_actions,'memory_writes':self.used['memory_writes']+memory_writes}; reasons=[]
        if p['steps']>self.budget.max_steps: reasons.append('max_steps_exceeded')
        if p['device_actions']>self.budget.max_device_actions: reasons.append('max_device_actions_exceeded')
        if p['high_risk_actions']>self.budget.max_high_risk_actions: reasons.append('max_high_risk_actions_exceeded')
        if p['memory_writes']>self.budget.max_memory_writes: reasons.append('max_memory_writes_exceeded')
        if time.time()-self.started_at>self.budget.max_seconds: reasons.append('max_seconds_exceeded')
        if not reasons: self.used=p
        return BudgetDecision(not reasons,reasons,{'steps':self.budget.max_steps-self.used['steps'],'device_actions':self.budget.max_device_actions-self.used['device_actions'],'high_risk_actions':self.budget.max_high_risk_actions-self.used['high_risk_actions'],'memory_writes':self.budget.max_memory_writes-self.used['memory_writes']})

@dataclass
class RunEvaluation:
    run_id: str; score: float; passed: bool; defects: List[str]; procedure_updates: List[str]; memory_updates: List[str]; created_at: float=field(default_factory=time.time)
class ContinuousImprovementEvaluator:
    def evaluate(self, run_id, receipts, acceptance):
        defects=[]
        for r in receipts:
            if r.get('status') in ['failed','blocked_by_dependency']: defects.append(f"receipt:{r.get('action_id')}:{r.get('status')}")
            if r.get('status')=='timeout_pending_verify': defects.append(f"pending_verify:{r.get('action_id')}")
        for c in acceptance:
            if c.get('required',True) and not c.get('passed',False): defects.append(f"acceptance:{c.get('name')}")
        score=max(0.0,1.0-.15*len(defects)); proc=[]
        if any('pending_verify' in d for d in defects): proc.append('prefer_two_phase_verification_for_timeout_actions')
        if not defects: proc.append('promote_current_workflow_as_successful_procedure_candidate')
        return RunEvaluation(run_id,score,not defects,defects,proc,[])
    def to_guarded_update_request(self, ev): return {'kind':'continuous_improvement_update','requires_memory_guard':True,'evaluation':asdict(ev)}

class AutonomousOSSupremeGate:
    required_flags=['six_layer_no_l7','goal_contract_ok','handoff_trace_ok','tool_guardrails_ok','device_saga_serial_ok','capability_extension_sandboxed','scenario_simulation_ok','autonomy_budget_ok','memory_guarded','continuous_evaluation_ok']
    def check(self, report):
        missing=[f for f in self.required_flags if report.get(f) is not True]; layer=[]
        if report.get('agent_kernel_layer') not in [None,'L3']: layer.append('agent_kernel_not_l3')
        if report.get('has_l7') is True: layer.append('l7_detected')
        return {'gate':'V45.0_autonomous_os_supreme_gate','pass':not missing and not layer,'missing':missing,'layer_violations':layer}
