from dataclasses import dataclass,asdict
import json
@dataclass
class WorldCapability:
    name:str; kind:str; status:str='available'; scopes:list=None; requires_approval:bool=False; trust_level:str='local'
    def __post_init__(self): self.scopes=self.scopes or []
class WorldInterfaceRegistry:
    def __init__(self): self._items={}
    def register(self,cap):
        if cap.kind not in {'local','connector','mcp','file','api','device'}: raise ValueError('bad kind')
        self._items[cap.name]=cap
    def resolve(self,need,required_scope=None,min_trust=None):
        out=[]
        for c in self._items.values():
            if need.lower() not in (' '.join([c.name,c.kind]+c.scopes)).lower(): continue
            if required_scope and required_scope not in c.scopes: continue
            if min_trust and c.trust_level!=min_trust: continue
            out.append(asdict(c))
        return sorted(out,key=lambda x:(x['requires_approval'],x['kind'],x['name']))
    def missing(self,need): return not self.resolve(need)
    def export_contracts(self): return json.dumps({k:asdict(v) for k,v in sorted(self._items.items())},ensure_ascii=False,indent=2)
