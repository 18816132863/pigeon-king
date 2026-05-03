from dataclasses import dataclass,asdict
from datetime import datetime,timezone
@dataclass
class JudgeDecision:
    decision:str; risk_tier:str; reasons:list; approval_required:bool; created_at:str=''
    def __post_init__(self):
        if not self.created_at: self.created_at=datetime.now(timezone.utc).isoformat()
    def to_dict(self): return asdict(self)
class UnifiedJudge:
    HARD={'exfiltrate_secret','bypass_auth','disable_safety','irreversible_delete_without_backup'}; APPROVAL={'send_external','payment','purchase','install_code','delete','publish','calendar_invite'}
    def decide(self,action,user_profile=None,runtime=None):
        user_profile=user_profile or {}; runtime=runtime or {}; name=str(action.get('action','unknown'))
        if name in self.HARD: return JudgeDecision('block','L5',['hard_codex_block'],False)
        risk='L4' if action.get('destructive') or name in {'delete','payment','purchase','install_code'} else ('L3' if action.get('external') or name in {'send_external','publish','calendar_invite'} else ('L2' if action.get('mutates_state') else 'L1'))
        if runtime.get('context_confidence',1)<.55: return JudgeDecision('require_clarification',risk,['low_context_confidence'],False)
        if user_profile.get('no_auto_external_send') and name=='send_external': return JudgeDecision('require_approval','L3',['user_preference_no_auto_external_send'],True)
        if name in self.APPROVAL or risk in {'L3','L4'}: return JudgeDecision('require_approval',risk,['approval_required_by_risk_tier'],True)
        return JudgeDecision('allow',risk,['allowed_by_unified_judge'],False)
