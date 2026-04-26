class CommandIntentCompiler:
    """Compile one-sentence command into executive intent."""

    def compile(self, command: str) -> dict:
        return {
            "status": "compiled",
            "raw": command,
            "intent": "complete_goal",
            "needs_artifact": any(k in command for k in ["压缩包", "文件", "发给我"]),
            "needs_external_connection": any(k in command for k in ["外部", "真实", "API", "设备", "账号"]),
            "needs_self_extension": any(k in command for k in ["没技能", "没方案", "自动安装", "找方案"]),
            "style": "direct_complete" if any(k in command for k in ["一次性", "直接", "不要猜"]) else "balanced",
        }
