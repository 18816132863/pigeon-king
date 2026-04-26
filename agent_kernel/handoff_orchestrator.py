from dataclasses import dataclass,asdict
from datetime import datetime,timezone
@dataclass
class Specialist: name:str; role:str; capabilities:list
@dataclass
class HandoffRecord:
    from_agent:str; to_agent:str; reason:str; payload:dict; result:dict; created_at:str=''
    def __post_init__(self):
        if not self.created_at: self.created_at=datetime.now(timezone.utc).isoformat()
class HandoffOrchestrator:
    def __init__(self): self.specialists={}; self.handlers={}; self.records=[]
    def register(self,specialist,handler=None): self.specialists[specialist.name]=specialist; self.handlers.update({specialist.name:handler} if handler else {})
    def choose(self,need):
        for s in self.specialists.values():
            if any(need.lower() in c.lower() for c in s.capabilities): return s
        raise KeyError('no specialist')
    def handoff(self,from_agent,need,payload):
        s=self.choose(need); h=self.handlers.get(s.name,lambda p:{'ok':True,'handled_by':s.name}); result=h(payload); self.records.append(HandoffRecord(from_agent,s.name,'need:'+need,payload,result)); return result
    def trace(self): return [asdict(r) for r in self.records]
