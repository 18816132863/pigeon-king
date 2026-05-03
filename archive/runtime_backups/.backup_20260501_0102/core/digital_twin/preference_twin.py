class PreferenceTwin:
    def infer(self, signals: list[dict]) -> dict:
        text = " ".join(str(s) for s in signals)
        return {
            "style": "direct" if "直接" in text or "一次性" in text else "balanced",
            "artifact_first": "压缩包" in text or "文件" in text,
            "avoid": ["反复确认低风险问题", "让对方猜", "只说下一步不交付"],
        }
