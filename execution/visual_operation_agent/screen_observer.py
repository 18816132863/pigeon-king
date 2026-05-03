"""屏幕观察器 — 通过 xiaoyi_gui_agent 观察手机屏幕状态"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScreenState:
    """屏幕状态"""
    timestamp: str
    app_name: str
    page_name: str
    elements: list
    screenshot_path: Optional[str] = None
    raw_response: Optional[Any] = None


class ScreenObserver:
    """屏幕观察器。

    通过 xiaoyi_gui_agent 工具观察当前手机屏幕状态。
    """

    def __init__(self, tool_executor: Optional[Callable[[str], Any]] = None):
        self._last_state: Optional[ScreenState] = None
        self.tool_executor = tool_executor

    def observe(self, query: str = "") -> ScreenState:
        """观察当前屏幕。

        Args:
            query: 观察指令，如"截取当前屏幕"、"查看当前页面有什么"

        Returns:
            ScreenState
        """
        if self.tool_executor is None:
            return ScreenState(
                timestamp=datetime.now().isoformat(),
                app_name="unknown",
                page_name="unknown",
                elements=[],
            )

        observation_query = query or "查看当前屏幕显示什么内容"
        try:
            result = self.tool_executor(observation_query)
            state = ScreenState(
                timestamp=datetime.now().isoformat(),
                app_name="unknown",
                page_name="unknown",
                elements=[],
                raw_response=result,
            )
        except Exception as e:
            state = ScreenState(
                timestamp=datetime.now().isoformat(),
                app_name="unknown",
                page_name="unknown",
                elements=[],
                raw_response={"error": str(e)},
            )

        self._last_state = state
        return state

    def screenshot(self) -> ScreenState:
        """截取屏幕截图。"""
        return self.observe("截取当前屏幕截图")

    def get_current_app(self) -> str:
        """获取当前前台应用名。"""
        if self._last_state:
            return self._last_state.app_name
        return "unknown"

    def get_last_state(self) -> Optional[ScreenState]:
        """获取最后一次观察结果。"""
        return self._last_state

    def detect_change(self) -> bool:
        """检测屏幕是否变化（简单实现）。"""
        if self._last_state is None:
            return True
        new_state = self.observe()
        return new_state.timestamp != self._last_state.timestamp

    def set_executor(self, executor: Callable[[str], Any]):
        """设置工具执行器（xiaoyi_gui_agent）。"""
        self.tool_executor = executor
