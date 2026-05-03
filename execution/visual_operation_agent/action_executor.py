"""动作执行器 — 通过 xiaoyi_gui_agent 执行手机操作

支持两种模式：
- execute（真实）：通过回调调用 xiaoyi_gui_agent 操作手机
- plan（规划）：只生成操作计划，不真实执行
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ActionResult:
    """动作结果"""
    action: str
    success: bool
    message: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None


class ActionExecutor:
    """手机动作执行器。

    Args:
        tool_executor: xiaoyi_gui_agent 的调用回调，接受 query 字符串
        mode: "execute" 真实执行 / "plan" 仅规划
    """

    def __init__(
        self,
        tool_executor: Optional[Callable[[str], Any]] = None,
        mode: str = "execute",
    ):
        self.tool_executor = tool_executor
        self.mode = mode

    def execute_query(self, query: str) -> ActionResult:
        """执行一条 GUI 操作指令。"""
        if self.mode == "plan" or self.tool_executor is None:
            return ActionResult(
                action="gui",
                success=True,
                message=f"规划: {query[:50]}",
                timestamp=datetime.now().isoformat(),
                details={"query": query, "mode": "plan"},
            )

        try:
            result = self.tool_executor(query)
            return ActionResult(
                action="gui",
                success=True,
                message=f"已执行: {query[:40]}",
                timestamp=datetime.now().isoformat(),
                details={"query": query, "result": result},
            )
        except Exception as e:
            return ActionResult(
                action="gui",
                success=False,
                message=f"执行失败: {e}",
                timestamp=datetime.now().isoformat(),
                details={"error": str(e)},
            )

    def tap_by_text(self, text: str, app_context: str = "") -> ActionResult:
        """点击指定文本的按钮/链接。"""
        app_hint = f"在{app_context}中" if app_context else ""
        return self.execute_query(
            f"{app_hint}点击\"{text}\""
        )

    def type_text(self, text: str, into_field_hint: str = "") -> ActionResult:
        """输入文本。"""
        field_hint = f"在\"{into_field_hint}\"中输入" if into_field_hint else "输入"
        return self.execute_query(
            f"{field_hint}{text}"
        )

    def swipe(self, direction: str = "up", distance: str = "half") -> ActionResult:
        """滑动屏幕。"""
        return self.execute_query(
            f"向{direction}滑动{distance}屏"
        )

    def open_app(self, app_name: str) -> ActionResult:
        """打开应用。"""
        return self.execute_query(f"打开{app_name}")

    def back(self) -> ActionResult:
        """返回上一页。"""
        return self.execute_query("返回上一页")

    def home(self) -> ActionResult:
        """回到桌面。"""
        return self.execute_query("回到桌面")

    def scroll_to_bottom(self) -> ActionResult:
        """滚动到底部。"""
        return self.execute_query("滚动到底部")

    def scroll_to_top(self) -> ActionResult:
        """滚动到顶部。"""
        return self.execute_query("滚动到顶部")

    def take_screenshot(self) -> ActionResult:
        """截图。"""
        return self.execute_query("截取当前屏幕截图")

    def wait(self, seconds: int = 2) -> ActionResult:
        """等待。"""
        return self.execute_query(f"等待{seconds}秒")

    def batch(self, steps: List[str]) -> List[ActionResult]:
        """批量执行多个步骤。"""
        results = []
        for step in steps:
            result = self.execute_query(step)
            results.append(result)
            if not result.success:
                break
        return results

    def execute_plan(self, plan: List[Dict[str, Any]]) -> List[ActionResult]:
        """执行规划器生成的步骤列表。

        Args:
            plan: 规划器生成的步骤列表，每个步骤包含 action/params

        Returns:
            每个步骤的执行结果
        """
        results = []
        for step in plan:
            action = step.get("action", "")
            params = step.get("params", {})
            target = step.get("target", "")

            if action == "tap":
                if "text" in params:
                    results.append(self.tap_by_text(params["text"]))
                else:
                    results.append(self.execute_query(f"点击\"{target}\""))
            elif action == "type":
                results.append(self.type_text(params.get("text", ""), target))
            elif action == "swipe":
                results.append(self.swipe(params.get("direction", "up"), params.get("distance", "half")))
            elif action == "open_app":
                results.append(self.open_app(target or params.get("app", "")))
            elif action == "back":
                results.append(self.back())
            elif action == "home":
                results.append(self.home())
            elif action == "wait":
                results.append(self.wait(params.get("seconds", 2)))
            elif action == "screenshot":
                results.append(self.take_screenshot())
            elif action == "scroll":
                direction = params.get("direction", "down")
                if direction == "bottom":
                    results.append(self.scroll_to_bottom())
                else:
                    results.append(self.scroll_to_top())
            else:
                results.append(self.execute_query(str(step)))

        return results

    def set_mode(self, mode: str):
        """切换模式。"""
        self.mode = mode

    def set_executor(self, executor: Callable[[str], Any]):
        """设置工具执行器。"""
        self.tool_executor = executor
