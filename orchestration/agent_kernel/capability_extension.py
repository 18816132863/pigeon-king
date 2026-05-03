from dataclasses import dataclass,asdict
from datetime import datetime,timezone
@dataclass
class CapabilityGap: need:str; severity:str; reason:str
@dataclass
class ExtensionCandidate: name:str; source:str; kind:str; trust_level:str; declared_scopes:list; status:str='proposed'
@dataclass
class ExtensionEvaluation:
    candidate:str; passed:bool; score:float; reasons:list; created_at:str=''
    def __post_init__(self):
        if not self.created_at: self.created_at=datetime.now(timezone.utc).isoformat()
class CapabilityExtensionPipeline:
    TRUSTED={'local_registry','approved_connector_catalog','internal_skill_store'}; DANGER={'payment','secrets','shell','filesystem_write','network_wide'}
    def detect_gap(self,need,available_names): return None if any(need.lower() in x.lower() for x in available_names) else CapabilityGap(need,'medium','no_matching_capability_registered')
    def propose(self,gap,catalog): return sorted([c for c in catalog if gap.need.lower() in (c.name+' '+' '.join(c.declared_scopes)).lower()],key=lambda c:(c.source not in self.TRUSTED,c.name))
    def evaluate(self,c,smoke_test=None):
        reasons=[]
        if c.source not in self.TRUSTED: reasons.append('untrusted_source')
        bad=sorted(set(c.declared_scopes)&self.DANGER)
        if bad: reasons.append('dangerous_scope:'+','.join(bad))
        if smoke_test and not smoke_test(c): reasons.append('smoke_test_failed')
        return ExtensionEvaluation(c.name,not reasons,1.0 if not reasons else max(0,.6-.2*len(reasons)),reasons or ['sandbox_evaluation_passed'])
    def promote_or_quarantine(self,c,e): c.status='active' if e.passed else 'quarantined'; return {'candidate':asdict(c),'evaluation':asdict(e),'action':'promote' if e.passed else 'quarantine'}
