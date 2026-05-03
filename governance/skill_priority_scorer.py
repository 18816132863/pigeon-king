from governance.skill_intelligence_engine import SkillIntelligenceEngine
def score_skills(message, context=None, top_k=8): return SkillIntelligenceEngine().recommend_skills(message, context, top_k)
