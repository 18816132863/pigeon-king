from __future__ import annotations

from pathlib import Path
from typing import Dict
from .schemas import FeedbackRecord, FeedbackSignal, new_id, to_dict
from .storage import JsonStore


class FeedbackTrainer:
    """V163: converts user feedback into tentative personalization updates."""

    def __init__(self, root: str | Path = ".personalization_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "feedback_records.json")

    def ingest(self, message: str, target: str = "assistant_behavior") -> FeedbackRecord:
        if any(x in message for x in ["好", "对", "可以", "就这样", "欧克"]):
            signal = FeedbackSignal.POSITIVE
        elif any(x in message for x in ["不行", "错", "不要", "太麻烦", "一点点"]):
            signal = FeedbackSignal.CORRECTION
        elif any(x in message for x in ["差", "垃圾", "没用"]):
            signal = FeedbackSignal.NEGATIVE
        else:
            signal = FeedbackSignal.NEUTRAL

        updates: Dict[str, str] = {}
        if "不要一点点" in message or "一点点" in message:
            updates["interaction.style"] = "one_shot_not_incremental"
        if "压缩包" in message or "命令" in message:
            updates["delivery.mode"] = "package_and_command"
        if "太麻烦" in message:
            updates["verbosity"] = "shorter_command_first"

        rec = FeedbackRecord(
            id=new_id("feedback"),
            signal=signal,
            target=target,
            message=message,
            extracted_updates=updates,
        )
        self.store.append(to_dict(rec))
        return rec

    def count(self) -> int:
        return len(self.store.read([]))
