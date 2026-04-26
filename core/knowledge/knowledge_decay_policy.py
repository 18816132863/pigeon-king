class KnowledgeDecayPolicy:
    def classify(self, item: dict) -> dict:
        topic = item.get("topic", "")
        if any(k in topic for k in ["价格", "政策", "接口", "平台规则"]):
            decay = "fast"
        elif any(k in topic for k in ["架构", "个人偏好", "长期目标"]):
            decay = "slow"
        else:
            decay = "medium"
        return {"status": "classified", "decay": decay, "refresh_required": decay == "fast"}
