class IntentState:
    def parse(self, text: str) -> dict:
        return {
            "raw": text,
            "wants_autonomy": any(k in text for k in ["自动", "自己", "一句话", "不用问"]),
            "wants_artifact": any(k in text for k in ["压缩包", "文件", "直接发"]),
            "dislikes_guessing": any(k in text for k in ["不要猜", "别乱改", "不要浪费时间"]),
        }
