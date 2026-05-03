from governance.skill_intelligence_engine import recommend_skills, SkillIntelligenceEngine
def match_skills(user_message, context=None, top_k=8): return recommend_skills(user_message, context, top_k)
class ProactiveSkillMatcher:
    def __init__(self): self.engine=SkillIntelligenceEngine()
    def match(self,user_message,context=None,top_k=8): return self.engine.recommend_skills(user_message,context,top_k)
    def recommend(self,user_message,context=None,top_k=8): return self.match(user_message,context,top_k)
