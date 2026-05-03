import json, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; FEEDBACK=ROOT/'.skill_state'/'skill_usage_feedback.jsonl'
def record_feedback(skill_id, accepted=None, task_domain=None, result_quality=None, user_feedback=None):
    FEEDBACK.parent.mkdir(parents=True,exist_ok=True); entry={'ts':time.time(),'skill_id':skill_id,'accepted':accepted,'task_domain':task_domain,'result_quality':result_quality,'user_feedback':user_feedback}
    with FEEDBACK.open('a',encoding='utf-8') as f: f.write(json.dumps(entry,ensure_ascii=False)+'\n')
    return entry
