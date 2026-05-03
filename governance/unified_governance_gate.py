from __future__ import annotations
import os
from dataclasses import dataclass, asdict
from typing import Any
try:
    from infrastructure.unified_observability_ledger import record_event
except Exception:
    def record_event(*a, **k): return None
COMMIT_PATTERNS={
 'payment':['pay','payment','purchase','checkout','transfer','付款','支付','转账','下单'],
 'signature':['sign','signature','contract','签署','合同','签名'],
 'send':['send','email','publish','post','webhook','notify','发送','外发','发布','飞书'],
 'device':['device','robot','actuator','click','door','机械','设备','机器人','开门'],
 'delete':['delete','remove','drop','destroy','删除','销毁'],
 'identity_commitment':['commit identity','promise as user','代表用户承诺','身份承诺'],
}
@dataclass
class GovernanceDecision:
    allowed: bool; action_class: str; recommendation_mode: str; risk_class: str; reason: str; blocked_reason: str|None=None
    no_external_api: bool=False; no_real_send: bool=False; no_real_payment: bool=False; no_real_device: bool=False
    def to_dict(self): return asdict(self)

def classify_action(action: Any, context: dict|None=None):
    text=(str(action)+' '+str(context or {})).lower()
    for cls, keys in COMMIT_PATTERNS.items():
        if any(k.lower() in text for k in keys): return cls
    if any(k in text for k in ['http','requests','openai','api','calendar','web']): return 'external_api'
    return 'safe_dry_run'
class UnifiedGovernanceGate:
    def check_action(self, action: Any, context: dict|None=None):
        action_class=classify_action(action, context)
        env={'no_external_api':os.environ.get('NO_EXTERNAL_API')=='true','no_real_send':os.environ.get('NO_REAL_SEND')=='true','no_real_payment':os.environ.get('NO_REAL_PAYMENT')=='true','no_real_device':os.environ.get('NO_REAL_DEVICE')=='true'}
        if action_class in {'payment','signature','send','device','delete','identity_commitment'}:
            d=GovernanceDecision(False,action_class,'blocked','commit_high','commit action hard stopped',f'{action_class}_blocked',**env)
        elif action_class=='external_api' and env['no_external_api']:
            d=GovernanceDecision(False,action_class,'mock','external','external API blocked in offline mode','external_api_blocked',**env)
        else:
            d=GovernanceDecision(True,action_class,'dry_run','low','safe dry-run allowed',None,**env)
        record_event('governance_decision', d.to_dict()); return d

def check_action(action: Any, context: dict|None=None): return UnifiedGovernanceGate().check_action(action, context).to_dict()
