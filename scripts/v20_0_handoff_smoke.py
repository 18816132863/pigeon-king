from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from agent_kernel.handoff_orchestrator import HandoffOrchestrator,Specialist
h=HandoffOrchestrator(); h.register(Specialist('planner','goal planning',['plan','goal']),lambda p:{'planned':True,'goal':p.get('goal')}); r=h.handoff('root','plan',{'goal':'推进版本'}); assert r['planned'] and h.trace()[0]['to_agent']=='planner'; print(json.dumps({'v20_0_handoff':'pass','trace_len':len(h.trace())},ensure_ascii=False))
