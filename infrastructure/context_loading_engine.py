from __future__ import annotations
import json, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; LEDGER=ROOT/'.lazy_state'/'lazy_load_ledger.jsonl'
P0=['commit_barrier','offline_runtime_guard','mainline_hook','AGENTS.md','IDENTITY.md','MEMORY.md','context_capsule','session_handoff','CURRENT_RELEASE_INDEX','skill_policy_gate']; P1=['skill_trigger_registry','skill_profiles','proactive_skill_matcher','current_reports_summary','relationship_memory_summary']; P2=['full_skill_bodies','pdf_docx_excel_processors','gui_visual_agent','multimodal_index','old_reports','nvidia_gpu_modules','connector_factories']; P3=['external_api_skills','webhook_email_calendar_upload','real_payment_send_device_signature']
class UnifiedContextLoadingEngine:
    def __init__(self): LEDGER.parent.mkdir(parents=True,exist_ok=True)
    def _record(self,level,item,action):
        e={'ts':time.time(),'level':level,'item':item,'action':action}
        with LEDGER.open('a',encoding='utf-8') as f: f.write(json.dumps(e,ensure_ascii=False)+'\n')
        return e
    def preload_p0(self): return [self._record('P0',x,'preload') for x in P0]
    def warm_p1(self): return [self._record('P1',x,'warm') for x in P1]
    def lazy_load_p2(self,item=None): return self._record('P2',item or 'on_demand','lazy_load')
    def block_p3(self,item=None): return self._record('P3',item or 'external_or_commit','block_or_mock')
    def status(self): return {'p0':P0,'p1':P1,'p2':P2,'p3':P3,'ledger':str(LEDGER),'ready':True}
def preload_p0(): return UnifiedContextLoadingEngine().preload_p0()
def warm_p1(): return UnifiedContextLoadingEngine().warm_p1()
def lazy_load_p2(item=None): return UnifiedContextLoadingEngine().lazy_load_p2(item)
def block_p3(item=None): return UnifiedContextLoadingEngine().block_p3(item)
