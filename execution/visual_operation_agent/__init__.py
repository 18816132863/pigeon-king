"""视觉操作智能体 — 通过 xiaoyi_gui_agent 真机操作

提供将用户指令解析为手机操作步骤、执行、反馈的完整闭环。

组件:
- ScreenObserver   — 观察手机屏幕状态
- UIGrounding      — 解析 UI 元素描述
- ActionExecutor   — 执行手机操作指令
- VisualPlanner    — 将目标分解为操作步骤序列

使用方式:
    executor = ActionExecutor(tool_executor=xiaoyi_gui_agent)
    planner = VisualPlanner()

    # 规划 + 执行
    steps = planner.plan_for_goal("打开微信搜索张三")
    results = executor.execute_plan([asdict(s) for s in steps])
"""

from .screen_observer import ScreenObserver, ScreenState
from .ui_grounding import UIGrounding, UIElement
from .action_executor import ActionExecutor, ActionResult
from .visual_planner import VisualPlanner, VisualStep

__all__ = [
    "ScreenObserver",
    "ScreenState",
    "UIGrounding",
    "UIElement",
    "ActionExecutor",
    "ActionResult",
    "VisualPlanner",
    "VisualStep",
]
