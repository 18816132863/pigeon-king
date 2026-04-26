from dataclasses import dataclass,asdict
from datetime import datetime,timezone
from pathlib import Path
import importlib,json
REQUIRED=['agent_kernel.goal_compiler','agent_kernel.task_graph','agent_kernel.memory_kernel','agent_kernel.unified_judge','agent_kernel.world_interface','agent_kernel.capability_extension','agent_kernel.handoff_orchestrator','agent_kernel.persona_kernel','agent_kernel.autonomous_loop','agent_kernel.meta_governance']
@dataclass
class GateReport: release:str; status:str; checks:dict; created_at:str
class MetaGovernanceGate:
    def run(self):
        checks={}; missing=[]
        for m in REQUIRED:
            try: importlib.import_module(m); checks[m]='ok'
            except Exception as e: checks[m]='failed:'+str(e); missing.append(m)
        return GateReport('V23.0','pass' if not missing else 'fail',checks,datetime.now(timezone.utc).isoformat())
    def write_report(self,path):
        data=asdict(self.run()); Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True),encoding='utf-8'); return data
