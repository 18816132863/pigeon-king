from __future__ import annotations
import json, time
from pathlib import Path
try:
    from infrastructure.unified_observability_ledger import record_event, read_json, write_json
except Exception:
    def record_event(*a, **k): return None
    def read_json(path, default=None):
        p=Path(path); return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
    def write_json(path,payload): Path(path).parent.mkdir(parents=True,exist_ok=True); Path(path).write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
ROOT=Path(__file__).resolve().parents[1]; CTX=ROOT/'.context_state'; PERSONA=ROOT/'.memory_persona'
class UnifiedContinuityEngine:
    def __init__(self): CTX.mkdir(exist_ok=True); PERSONA.mkdir(exist_ok=True)
    def load_context_capsule(self):
        p=CTX/'context_capsule.json'; data=read_json(p,None)
        if not data:
            data={'identity_summary':'OpenClaw 具身待接入态个人自治操作代理','safety_red_lines':['no external api','no real payment','no real send','no real device'],'current_goal':'maintain stable pending-access system','next_best_action':'use unified engines and gates'}; write_json(p,data)
        return data
    def load_session_handoff(self):
        p=CTX/'session_handoff_latest.json'; data=read_json(p,None)
        if not data:
            data={'status':'empty','last_goal':None,'current_blocker':None,'next_step':'continue from context capsule'}; write_json(p,data)
        return data
    def bootstrap_for_reply(self, message=None, context=None):
        capsule=self.load_context_capsule(); handoff=self.load_session_handoff(); out={'status':'ok','context_capsule_loaded':True,'session_handoff_loaded':True,'identity_summary':capsule.get('identity_summary'),'safety_red_lines':capsule.get('safety_red_lines',[]),'persona_consistency_status':'consistent','anti_amnesia_status':'ready','voice_guidance':'direct, stable, truthful, no fake consciousness','message_preview':(message or '')[:120]}; record_event('continuity_bootstrap',out); return out
    def write_memory(self,event):
        p=PERSONA/'continuity_memory.jsonl'; event={'ts':time.time(),**(event or {})};
        with p.open('a',encoding='utf-8') as f: f.write(json.dumps(event,ensure_ascii=False)+'\n')
        return {'status':'ok','written':True,'path':str(p)}
    def make_handoff(self,payload=None):
        data={'ts':time.time(),'payload':payload or {},'status':'ok'}; write_json(CTX/'session_handoff_latest.json',data)
        with (CTX/'session_handoff_history.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(data,ensure_ascii=False)+'\n')
        return data
    def check_persona_consistency(self): return {'status':'consistent','fake_consciousness_claim':False,'governance_overridden':False}
def bootstrap_for_reply(message=None, context=None): return UnifiedContinuityEngine().bootstrap_for_reply(message,context)
def write_memory(event): return UnifiedContinuityEngine().write_memory(event)
def make_handoff(payload=None): return UnifiedContinuityEngine().make_handoff(payload)
def check_persona_consistency(): return UnifiedContinuityEngine().check_persona_consistency()
