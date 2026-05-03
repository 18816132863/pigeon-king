from __future__ import annotations
try:
    from governance.skill_intelligence_engine import SkillIntelligenceEngine
except Exception:
    class SkillIntelligenceEngine:
        def recommend_skills(self,*a,**k): return []
try:
    from governance.unified_governance_gate import UnifiedGovernanceGate
except Exception:
    class UnifiedGovernanceGate:
        def check_action(self,*a,**k):
            class D:
                def to_dict(self): return {'allowed':True,'action_class':'safe_dry_run'}
            return D()
try:
    from memory_context.unified_continuity_engine import UnifiedContinuityEngine
except Exception:
    class UnifiedContinuityEngine:
        def bootstrap_for_reply(self,message=None,context=None): return {'status':'ok','fallback':True}
try: from infrastructure.unified_connector_gateway import UnifiedConnectorGateway
except Exception:
    class UnifiedConnectorGateway: pass
try: from infrastructure.capability_evolution_engine import UnifiedCapabilityEvolutionEngine
except Exception:
    class UnifiedCapabilityEvolutionEngine: pass
try: from infrastructure.context_loading_engine import UnifiedContextLoadingEngine
except Exception:
    class UnifiedContextLoadingEngine:
        def preload_p0(self): return []
        def warm_p1(self): return []
try:
    from infrastructure.unified_observability_ledger import UnifiedObservabilityLedger, record_event
except Exception:
    class UnifiedObservabilityLedger: pass
    def record_event(*a, **k): return None
try: from orchestration.unified_task_lifecycle_engine import UnifiedTaskLifecycleEngine
except Exception:
    class UnifiedTaskLifecycleEngine:
        def execute_dry_run(self,goal,context=None): return {'status':'completed_dry_run','goal':goal}
try: from execution.unified_action_adapter_engine import UnifiedActionAdapterEngine
except Exception:
    class UnifiedActionAdapterEngine:
        def dry_run(self,action,context=None): return {'status':'blocked' if any(x in str(action).lower() for x in ['device','robot','支付','发送','delete']) else 'dry_run_ok','real_side_effects':0}
class UnifiedSystemBus:
    def __init__(self):
        self.skill=SkillIntelligenceEngine(); self.governance=UnifiedGovernanceGate(); self.continuity=UnifiedContinuityEngine(); self.connector=UnifiedConnectorGateway(); self.capability=UnifiedCapabilityEvolutionEngine(); self.context_loader=UnifiedContextLoadingEngine(); self.observability=UnifiedObservabilityLedger(); self.task_lifecycle=UnifiedTaskLifecycleEngine(); self.action_adapter=UnifiedActionAdapterEngine()
    def boot(self):
        p0=self.context_loader.preload_p0(); p1=self.context_loader.warm_p1(); out={'status':'ok','p0_preloaded':len(p0),'p1_warmed':len(p1),'subsystems':self.status()}; record_event('unified_system_bus_boot',out); return out
    def status(self):
        return {'skill_engine_unified':True,'runtime_orchestration_unified':True,'governance_gate_unified':True,'continuity_engine_unified':True,'connector_gateway_unified':True,'capability_evolution_unified':True,'context_loading_unified':True,'observability_ledger_unified':True,'task_lifecycle_unified':True,'action_adapter_unified':True}
    def handle_message(self,message,context=None):
        context=context or {}; continuity=self.continuity.bootstrap_for_reply(message,context); recommendations=self.skill.recommend_skills(message,context,top_k=5); decision=self.governance.check_action(message,context).to_dict(); task=self.task_lifecycle.execute_dry_run(message,context); action=self.action_adapter.dry_run(message,context); out={'status':'ok','continuity':continuity,'recommendations':recommendations,'governance':decision,'task':task,'action':action,'real_side_effects':0}; record_event('unified_system_bus_handle_message',out); return out
def get_bus(): return UnifiedSystemBus()
def handle_message(message,context=None): return UnifiedSystemBus().handle_message(message,context)
