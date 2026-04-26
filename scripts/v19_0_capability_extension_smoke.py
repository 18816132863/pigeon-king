from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

from agent_kernel.capability_extension import CapabilityExtensionPipeline,ExtensionCandidate
p=CapabilityExtensionPipeline(); gap=p.detect_gap('calendar',['file_reader']); c=p.propose(gap,[ExtensionCandidate('calendar_connector','approved_connector_catalog','connector','approved',['calendar','read']),ExtensionCandidate('calendar_shell','random_web','package','unknown',['calendar','shell'])])[0]; ev=p.evaluate(c); res=p.promote_or_quarantine(c,ev); assert res['action']=='promote'; bad=p.evaluate(ExtensionCandidate('calendar_shell','random_web','package','unknown',['calendar','shell'])); assert not bad.passed; print(json.dumps({'v19_0_capability_extension':'pass','promoted':res['candidate']['name']},ensure_ascii=False))
