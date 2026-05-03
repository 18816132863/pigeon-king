from __future__ import annotations

from pathlib import Path
from .schemas import UserProfile, new_id, to_dict, now_ts
from .storage import JsonStore


class UserProfileModel:
    """V157: user profile model."""

    def __init__(self, root: str | Path = ".personalization_state"):
        self.root = Path(root)
        self.store = JsonStore(self.root / "user_profile.json")
        self._ensure_default()

    def _ensure_default(self) -> None:
        if self.store.read(None):
            return
        profile = UserProfile(
            id=new_id("profile"),
            display_name="用户",
            working_style="直接、结果导向、少废话",
            delivery_style="一次性压缩包 + 一条命令 + 验收标准",
            risk_style="高风险强审批，低风险自动推进",
            language="zh",
            confidence=0.78,
        )
        self.store.write(to_dict(profile))

    def get(self) -> UserProfile:
        item = self.store.read({})
        return UserProfile(
            id=item["id"],
            display_name=item.get("display_name", "用户"),
            working_style=item.get("working_style", ""),
            delivery_style=item.get("delivery_style", ""),
            risk_style=item.get("risk_style", ""),
            language=item.get("language", "zh"),
            updated_at=float(item.get("updated_at", now_ts())),
            confidence=float(item.get("confidence", 0.7)),
        )

    def update(self, **kwargs) -> UserProfile:
        profile = self.get()
        data = to_dict(profile)
        for k, v in kwargs.items():
            if k in data and v is not None:
                data[k] = v
        data["updated_at"] = now_ts()
        data["confidence"] = min(1.0, float(data.get("confidence", 0.7)) + 0.03)
        self.store.write(data)
        return self.get()
