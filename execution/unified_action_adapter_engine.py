from __future__ import annotations
try:
    from governance.unified_governance_gate import UnifiedGovernanceGate
    from infrastructure.unified_observability_ledger import record_event
except Exception:
    UnifiedGovernanceGate=None
    def record_event(*a, **k): return None
class UnifiedActionAdapterEngine:
    def __init__(self): self.gate=UnifiedGovernanceGate() if UnifiedGovernanceGate else None
    def observe(self,target=None):
        out={'status':'ok','action':'observe','target':target,'real_side_effects':0}; record_event('action_observe',out); return out
    def plan(self,goal):
        out={'status':'ok','action':'plan','goal':goal,'steps':['observe','analyze','prepare'],'real_side_effects':0}; record_event('action_plan',out); return out
    def dry_run(self,action,context=None):
        d=self.gate.check_action(action,context or {}).to_dict() if self.gate else {'allowed':True}; out={'status':'blocked' if not d.get('allowed') else 'dry_run_ok','action':action,'decision':d,'real_side_effects':0}; record_event('action_dry_run',out); return out
    def mock_device(self,action):
        out={'status':'mocked','action':action,'device_connected':False,'real_side_effects':0}; record_event('action_mock_device',out); return out
def dry_run(action,context=None): return UnifiedActionAdapterEngine().dry_run(action,context)
