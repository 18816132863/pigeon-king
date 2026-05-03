class BehaviorPatternMiner:
    def mine(self, events: list[dict]) -> dict:
        direct_count = sum(1 for e in events if "直接" in str(e) or "不要猜" in str(e))
        return {
            "status": "mined",
            "patterns": {
                "direct_execution_preference": direct_count > 0,
                "artifact_delivery_preference": any("压缩包" in str(e) or "文件" in str(e) for e in events),
            },
        }
