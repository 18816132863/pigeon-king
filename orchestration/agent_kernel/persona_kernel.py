from dataclasses import dataclass,asdict
@dataclass
class PersonaProfile:
    name:str='小艺'; response_style:str='direct_actionable'; autonomy_level:str='controlled_autonomy'; risk_posture:str='confirm_high_risk'; preferred_artifacts:str='zip_or_file_when_useful'; interaction_rules:list=None
    def __post_init__(self): self.interaction_rules=self.interaction_rules or ['avoid_repetitive_clarification','prefer_concrete_plan','surface_failures_honestly','high_risk_requires_confirmation']
class PersonaKernel:
    def __init__(self,profile=None): self.profile=profile or PersonaProfile()
    def apply_to_goal_context(self,context):
        x=dict(context); x.setdefault('priority','normal'); x['persona']=asdict(self.profile); x['no_auto_external_send']=self.profile.risk_posture=='confirm_high_risk'; return x
    def policy_profile(self): return {'no_auto_external_send':self.profile.risk_posture=='confirm_high_risk','autonomy_level':self.profile.autonomy_level,'response_style':self.profile.response_style}
