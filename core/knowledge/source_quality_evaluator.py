class SourceQualityEvaluator:
    def evaluate(self, source: dict) -> dict:
        source_type = source.get("type", "unknown")
        trusted = source_type in {"official_doc", "local_verified", "user_provided", "internal_report"}
        recency = source.get("recency", "unknown")
        return {
            "status": "evaluated",
            "trusted": trusted,
            "quality_score": 90 if trusted else 50,
            "requires_cross_check": not trusted or recency == "unknown",
        }
