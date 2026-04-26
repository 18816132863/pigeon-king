"""V12.2 deterministic local replay harness."""
from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
from platform_adapter.runtime_state_store import register_action, enqueue_action, get_action, summarize_runtime, transition_action
from platform_adapter.delivery_outbox import lease_next, mark_delivered, mark_failed, outbox_summary
from platform_adapter.trace_recorder import record_trace, build_trace_report

def default_replay_plan()->List[Dict[str,Any]]:
    return [{'step':'register','capability':'device.notification','op_name':'send','payload':{'title':'smoke'},'risk_level':'L2'},{'step':'enqueue','delivery_mode':'confirm_then_queue'},{'step':'lease','limit':1},{'step':'deliver','result':{'ok':True,'provider':'local_smoke'}}]

def timeout_replay_plan()->List[Dict[str,Any]]:
    return [{'step':'register','capability':'device.sms','op_name':'send','payload':{'to':'10086','body':'smoke'},'risk_level':'L3'},{'step':'enqueue','delivery_mode':'queued_for_delivery'},{'step':'lease','limit':1},{'step':'fail','error':'simulated_timeout','side_effecting':True,'result_uncertain':True}]

def run_replay_plan(plan:Optional[List[Dict[str,Any]]]=None, *, db_path:Optional[Path]=None, correlation_id:str='replay')->Dict[str,Any]:
    plan=list(plan or default_replay_plan()); results=[]; action_id=None; queue_id=None
    try:
        for item in plan:
            step=item.get('step'); record_trace(stage=f'replay.{step}', status='start', payload=item, action_id=action_id, correlation_id=correlation_id, db_path=db_path)
            if step=='register':
                a=register_action(capability=item.get('capability','device.unknown'), op_name=item.get('op_name','run'), payload=item.get('payload') or {}, risk_level=item.get('risk_level','L1'), db_path=db_path); action_id=a.action_id; detail=a.to_dict()
            elif step=='enqueue':
                queue_id=enqueue_action(action_id, delivery_mode=item.get('delivery_mode','queued_for_delivery'), db_path=db_path); detail={'queue_id':queue_id,'action_id':action_id}
            elif step=='lease':
                leased=lease_next(limit=int(item.get('limit',1)), db_path=db_path); assert leased, 'no leased item'; queue_id=int(leased[0]['queue_id']); action_id=leased[0]['action_id']; detail={'leased':leased}
            elif step=='deliver':
                detail=mark_delivered(int(queue_id), result=item.get('result') or {'ok':True}, db_path=db_path)
            elif step=='fail':
                detail=mark_failed(int(queue_id), error=item.get('error','simulated_failure'), side_effecting=bool(item.get('side_effecting',True)), result_uncertain=bool(item.get('result_uncertain',True)), db_path=db_path)
            elif step=='transition':
                detail=transition_action(action_id, item.get('to_state','completed'), reason='replay_transition', result=item.get('result'), db_path=db_path).to_dict()
            else: raise RuntimeError(f'unknown step {step}')
            record_trace(stage=f'replay.{step}', status='ok', payload=detail, action_id=action_id, correlation_id=correlation_id, db_path=db_path); results.append({'step':step,'ok':True,'detail':detail})
    except Exception as exc:
        record_trace(stage='replay', status='error', message=str(exc), action_id=action_id, correlation_id=correlation_id, db_path=db_path); results.append({'step':'error','ok':False,'detail':{'error':str(exc)}})
    failed=[r for r in results if not r['ok']]
    return {'gate':'pass' if not failed else 'fail','failed_steps':failed,'steps':results,'final_action':get_action(action_id, db_path=db_path).to_dict() if action_id else None,'runtime':summarize_runtime(db_path),'outbox':outbox_summary(db_path),'trace':{k:v for k,v in build_trace_report(correlation_id=correlation_id, db_path=db_path).items() if k!='events'}}

def run_default_replay(*, db_path:Optional[Path]=None)->Dict[str,Any]: return run_replay_plan(default_replay_plan(), db_path=db_path, correlation_id='default_replay')
