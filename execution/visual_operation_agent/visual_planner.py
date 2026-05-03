"""视觉规划器 — 为目标生成手机操作步骤序列"""

from __future__ import annotations

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class VisualStep:
    """视觉步骤"""
    step_id: int
    action: str  # tap, type, swipe, open_app, back, home, wait, screenshot, scroll
    target: str  # 目标描述
    params: Dict[str, Any]
    expected_result: str


class VisualPlanner:
    """手机操作规划器。

    将用户目标解析为一系列手机操作步骤。
    每个步骤可以被 ActionExecutor 执行。
    """

    def plan_for_goal(self, goal: str, app_name: str = "") -> List[VisualStep]:
        """为目标规划操作步骤。"""
        steps: List[VisualStep] = []
        step_id = 0

        goal_lower = goal.lower()

        # 1. 如果需要打开特定应用
        if app_name:
            step_id += 1
            steps.append(VisualStep(
                step_id=step_id,
                action="open_app",
                target=app_name,
                params={"app": app_name},
                expected_result=f"{app_name}已打开",
            ))

        # 2. 打开应用后等待
        if app_name or "打开" in goal:
            step_id += 1
            steps.append(VisualStep(
                step_id=step_id,
                action="wait",
                target="等待加载",
                params={"seconds": 2},
                expected_result="页面加载完成",
            ))

        # 3. 搜索类操作
        if "搜索" in goal or "查找" in goal or "查询" in goal:
            step_id += 1
            steps.append(VisualStep(
                step_id=step_id,
                action="tap",
                target="搜索框",
                params={"text": "搜索框"},
                expected_result="搜索框获得焦点",
            ))
            step_id += 1
            steps.append(VisualStep(
                step_id=step_id,
                action="type",
                target="搜索内容",
                params={"text": goal},
                expected_result="输入完成",
            ))

        # 4. 设置类操作
        if "设置" in goal or "开启" in goal or "关闭" in goal:
            step_id += 1
            steps.append(VisualStep(
                step_id=step_id,
                action="tap",
                target=goal,
                params={},
                expected_result=f"已{goal}",
            ))

        # 5. 滑动/滚动类
        if "滚动" in goal or "滑" in goal:
            direction = "向下" if "下" in goal else "向上" if "上" in goal else "向下"
            step_id += 1
            steps.append(VisualStep(
                step_id=step_id,
                action="scroll",
                target=direction,
                params={"direction": direction},
                expected_result=f"已{direction}滚动",
            ))

        # 6. 截图
        if "截图" in goal or "截图" in goal:
            step_id += 1
            steps.append(VisualStep(
                step_id=step_id,
                action="screenshot",
                target="截取屏幕",
                params={},
                expected_result="截图保存",
            ))

        # 7. 默认：先点击目标
        if not steps:
            step_id += 1
            steps.append(VisualStep(
                step_id=step_id,
                action="tap",
                target=goal.strip()[:30],
                params={},
                expected_result=f"已执行: {goal[:20]}",
            ))

        return steps

    def plan_to_app(self, app_name: str, target: str = "") -> List[VisualStep]:
        """规划打开应用并执行操作的完整路径。"""
        return self.plan_for_goal(target, app_name)

    def plan_search(self, keyword: str, app_name: str = "") -> List[VisualStep]:
        """规划搜索操作。"""
        if app_name:
            goal = f"在{app_name}中搜索{keyword}"
        else:
            goal = f"搜索{keyword}"
        return self.plan_for_goal(goal, app_name)

    def get_visual_path(self, app_name: str, goal: str) -> Dict[str, Any]:
        """获取完整的视觉操作路径。"""
        steps = self.plan_for_goal(goal, app_name)
        return {
            "app": app_name,
            "goal": goal,
            "steps": [
                {
                    "step_id": s.step_id,
                    "action": s.action,
                    "target": s.target,
                    "params": s.params,
                    "expected": s.expected_result,
                }
                for s in steps
            ],
            "total_steps": len(steps),
        }

    def format_steps_as_prompt(self, steps: List[VisualStep]) -> str:
        """将步骤转换为 xiaoyi_gui_agent 的指令。"""
        lines = []
        for s in steps:
            action_desc = {
                "tap": f"点击\"{s.target}\"",
                "type": f"输入\"{s.params.get('text', '')}\"",
                "swipe": f"向{s.params.get('direction', '上')}滑动",
                "open_app": f"打开{s.target}",
                "back": "返回上一页",
                "home": "回到桌面",
                "wait": f"等待{s.params.get('seconds', 2)}秒",
                "screenshot": "截取当前屏幕",
                "scroll": f"向{s.params.get('direction', '下')}滚动",
            }
            desc = action_desc.get(s.action, str(s.action))
            lines.append(f"{s.step_id}. {desc}")
        return "\n".join(lines)
