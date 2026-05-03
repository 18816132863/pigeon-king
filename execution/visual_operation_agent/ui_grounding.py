"""UI 定位 — 从 xiaoyi_gui_agent 返回结果中解析 UI 元素"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass


@dataclass
class UIElement:
    """UI 元素"""
    element_id: str
    element_type: str  # button, text, input, image, link, switch
    text: str
    bounds: Dict[str, int]  # x, y, width, height
    clickable: bool = True
    visible: bool = True


class UIGrounding:
    """基于文本描述的 UI 定位器。

    通过 xiaoyi_gui_agent 的描述文本解析出 UI 元素。
    不需要真实的手机截图/AccessibilityNode，纯文本驱动。
    """

    def parse_gui_response(self, raw: str) -> List[UIElement]:
        """从 xiaoyi_gui_agent 返回的文本中解析 UI 元素。

        支持格式：
        - "有按钮'确定'、按钮'取消'" 
        - "看到输入框、搜索框、列表"
        - "当前页面有返回按钮底部有导航栏"
        """
        elements = []
        if not raw:
            return elements

        # 从描述中提取按钮、输入框、链接等
        patterns = [
            (r"按钮['\"\u201c]?(\S+?)['\"\u201d]?", "button"),
            (r"输入框['\"\u201c]?(\S+?)['\"\u201d]?", "input"),
            (r"链接['\"\u201c]?(\S+?)['\"\u201d]?", "link"),
            (r"开关['\"\u201c]?(\S+?)['\"\u201d]?", "switch"),
            (r"图片['\"\u201c]?(\S+?)['\"\u201d]?", "image"),
        ]
        for pattern, element_type in patterns:
            matches = re.findall(pattern, raw)
            uid = 0
            for text in matches:
                uid += 1
                elements.append(UIElement(
                    element_id=f"{element_type}_{uid}",
                    element_type=element_type,
                    text=text.strip(),
                    bounds={"x": 0, "y": 0, "width": 100, "height": 40},
                    clickable=element_type in ("button", "link", "switch"),
                ))

        # 如果没解析出特定元素，用"关键词"提取
        if not elements:
            # 常见的可点击元素关键词
            keywords = ["确定", "取消", "保存", "删除", "编辑", "搜索", "返回", "提交",
                       "确认", "关闭", "设置", "更多", "下一步", "完成", "同意"]
            for kw in keywords:
                if kw in raw:
                    elements.append(UIElement(
                        element_id=f"keyword_{kw}",
                        element_type="button",
                        text=kw,
                        bounds={"x": 0, "y": 0, "width": 80, "height": 36},
                    ))

        return elements

    def locate_by_text(self, text: str, elements: List[UIElement]) -> Optional[UIElement]:
        """通过文本定位元素。"""
        for elem in elements:
            if text in elem.text:
                return elem
        return None

    def locate_by_type(self, element_type: str, elements: List[UIElement]) -> List[UIElement]:
        """通过类型定位元素。"""
        return [e for e in elements if e.element_type == element_type]

    def locate_button(self, text: str, elements: List[UIElement]) -> Optional[UIElement]:
        """定位按钮。"""
        for elem in elements:
            if elem.element_type == "button" and text in elem.text:
                return elem
        return None

    def locate_input(self, hint: str, elements: List[UIElement]) -> Optional[UIElement]:
        """定位输入框。"""
        for elem in elements:
            if elem.element_type == "input" and (hint in elem.text or hint == ""):
                return elem
        return None

    def get_actionable_elements(self, elements: List[UIElement]) -> List[UIElement]:
        """获取所有可点击的元素。"""
        return [e for e in elements if e.clickable]
