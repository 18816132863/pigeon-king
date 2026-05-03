"""
Dependency-free scene classifier for the V85 model decision engine.

The classifier deliberately uses deterministic rules first.  It should be fast,
cheap and stable enough to run for every incoming message before any model call.
"""

from __future__ import annotations

import re
from typing import Any, Iterable, List

from core.llm.schemas import (
    Complexity,
    CostPreference,
    LatencyPreference,
    PrivacyLevel,
    TaskCategory,
    TaskProfile,
)


def _contains_any(text: str, words: Iterable[str], signals: List[str], label: str) -> bool:
    hit = [w for w in words if w.lower() in text]
    if hit:
        signals.append(f"{label}:{','.join(hit[:5])}")
        return True
    return False


def _count_hits(text: str, words: Iterable[str]) -> int:
    return sum(1 for w in words if w.lower() in text)


def _looks_english(text: str) -> bool:
    letters = sum(ch.isalpha() and ord(ch) < 128 for ch in text)
    cjk = sum('\u4e00' <= ch <= '\u9fff' for ch in text)
    return letters > cjk * 2 and letters > 10


def classify_scene(
    query: str,
    has_image: bool = False,
    needs_code: bool = False,
    has_tools: bool = False,
    file_count: int = 0,
    attachment_types: List[str] | None = None,
    privacy_hint: str | None = None,
    **_: Any,
) -> TaskProfile:
    q = (query or "").strip()
    t = q.lower()
    signals: List[str] = []
    attachment_types = attachment_types or []

    profile = TaskProfile(query=q)
    profile.language = "en" if _looks_english(q) else "zh"
    profile.requires_tool_calling = bool(has_tools)
    profile.requires_file_access = file_count > 0 or bool(attachment_types)
    profile.requires_vision = bool(has_image) or any(x in {"image", "screenshot", "png", "jpg", "jpeg", "webp"} for x in attachment_types)
    profile.requires_audio = any(x in {"audio", "mp3", "wav", "m4a"} for x in attachment_types)

    if len(q) > 3000 or file_count >= 2 or any(x in {"zip", "tar", "gz", "pdf", "docx", "xlsx", "pptx"} for x in attachment_types):
        profile.requires_long_context = True
        profile.context_estimate = min(max(len(q) * 2, 16000), 1000000)
        signals.append("long_context:file_or_long_query")
    elif len(q) > 600:
        profile.context_estimate = min(max(len(q) * 2, 8192), 131072)

    if profile.requires_vision:
        profile.category = TaskCategory.VISION
        profile.complexity = Complexity.MEDIUM
        signals.append("vision:attachment")

    if profile.requires_audio:
        profile.category = TaskCategory.AUDIO
        profile.complexity = Complexity.MEDIUM
        signals.append("audio:attachment")

    if _contains_any(t, ["生成图片", "画一张", "做头像", "海报", "logo", "改图", "图片编辑", "去除背景"], signals, "image_generation"):
        profile.category = TaskCategory.IMAGE_GENERATION
        profile.requires_image_generation = True
        profile.requires_tool_calling = True
        profile.complexity = Complexity.MEDIUM

    if _contains_any(t, ["生成视频", "视频", "sora", "分镜", "带货视频", "真人展示商品"], signals, "video_generation"):
        profile.category = TaskCategory.VIDEO_GENERATION
        profile.requires_video_generation = True
        profile.requires_tool_calling = True
        profile.complexity = Complexity.HIGH

    code_words = [
        "代码", "函数", "class ", "def ", "import ", "pytest", "traceback", "报错", "bug",
        "接口", "api", "sdk", "python", "javascript", "typescript", "react", "vue",
        "sql", "重构", "模块", "源码", "压缩包", "测试失败", "覆盖", "全量包",
    ]
    arch_words = [
        "架构", "六层", "模块", "系统设计", "决策引擎", "模型决策", "路由", "gateway",
        "注册表", "调度", "orchestration", "agent", "内核", "主流程", "接入规则",
    ]
    if needs_code or _contains_any(t, code_words, signals, "code"):
        profile.category = TaskCategory.CODE
        profile.requires_coding = True
        profile.complexity = Complexity.MEDIUM
    if _contains_any(t, ["debug", "报错", "traceback", "异常", "测试失败", "resourcewarning", "timeout", "超时"], signals, "debug"):
        profile.category = TaskCategory.DEBUGGING
        profile.requires_coding = True
        profile.complexity = Complexity.HIGH
    if _contains_any(t, arch_words, signals, "architecture"):
        profile.category = TaskCategory.ARCHITECTURE
        profile.requires_reasoning = True
        profile.requires_coding = True
        profile.complexity = Complexity.HIGH
    if profile.requires_file_access and profile.requires_coding and _contains_any(t, ["全量", "压缩包", "多文件", "一次性", "覆盖", "目录"], signals, "multi_file"):
        profile.category = TaskCategory.MULTI_FILE_REFACTOR
        profile.requires_long_context = True
        profile.complexity = Complexity.VERY_HIGH

    realtime_words = ["最新", "现在", "今天", "昨天", "价格", "政策", "规则", "查一下", "搜索", "官网", "联系方式", "电话", "新闻"]
    if _contains_any(t, realtime_words, signals, "realtime"):
        profile.requires_web = True
        if profile.category == TaskCategory.CHAT:
            profile.category = TaskCategory.SEARCH
            profile.complexity = Complexity.MEDIUM

    compliance_words = ["违法", "合规", "广告法", "资质", "许可证", "规则", "风险", "监管", "营业执照", "食品经营"]
    if _contains_any(t, compliance_words, signals, "compliance"):
        profile.category = TaskCategory.COMPLIANCE
        profile.requires_reasoning = True
        profile.requires_web = True
        profile.complexity = Complexity.HIGH

    ecommerce_words = ["抖店", "抖音", "团长", "直播", "带货", "卖点", "话术", "转化", "sku", "佣金", "商品", "定价"]
    if _contains_any(t, ecommerce_words, signals, "ecommerce") and profile.category in {TaskCategory.CHAT, TaskCategory.WRITING, TaskCategory.BUSINESS}:
        profile.category = TaskCategory.ECOMMERCE
        profile.complexity = Complexity.MEDIUM
        profile.requires_reasoning = True

    business_words = ["方案", "策略", "计划", "路线图", "怎么做", "商业", "利润", "成本", "模式", "起步", "跑通"]
    if _contains_any(t, business_words, signals, "business") and profile.category == TaskCategory.CHAT:
        profile.category = TaskCategory.BUSINESS
        profile.requires_reasoning = True
        profile.complexity = Complexity.MEDIUM

    if _contains_any(t, ["翻译", "译成", "翻成", "translate"], signals, "translation"):
        profile.category = TaskCategory.TRANSLATION
        profile.complexity = Complexity.LOW
    if _contains_any(t, ["总结", "摘要", "概括", "提炼"], signals, "summary") and profile.category not in {TaskCategory.ARCHITECTURE, TaskCategory.MULTI_FILE_REFACTOR}:
        profile.category = TaskCategory.SUMMARY
        profile.complexity = Complexity.MEDIUM
    if _contains_any(t, ["提取", "抽取", "结构化", "json", "表格", "字段"], signals, "extraction"):
        profile.category = TaskCategory.EXTRACTION
        profile.requires_json_output = "json" in t or "结构化" in t
        profile.complexity = Complexity.MEDIUM

    reasoning_words = ["为什么", "分析", "对比", "区别", "原理", "本质", "推理", "逻辑", "论证", "因果", "评估", "打分"]
    hits = _count_hits(t, reasoning_words)
    if hits >= 2 and profile.category in {TaskCategory.CHAT, TaskCategory.BUSINESS, TaskCategory.ECOMMERCE}:
        profile.category = TaskCategory.REASONING if hits >= 4 else profile.category
        profile.requires_reasoning = True
        profile.complexity = Complexity.HIGH if hits >= 3 else Complexity.MEDIUM
        signals.append(f"reasoning_hits:{hits}")

    if _contains_any(t, ["最强", "不要省钱", "最终版", "全面", "不要出错", "完整", "一步到位"], signals, "premium"):
        profile.quality_preference = CostPreference.PREMIUM
        profile.cost_preference = CostPreference.PREMIUM
        if profile.complexity == Complexity.LOW:
            profile.complexity = Complexity.MEDIUM
    if _contains_any(t, ["低成本", "省钱", "便宜", "先粗略", "批量", "快速"], signals, "cheap"):
        profile.cost_preference = CostPreference.LOW
    if _contains_any(t, ["实时", "立刻", "马上", "快点", "低延迟"], signals, "latency"):
        profile.latency_preference = LatencyPreference.REALTIME

    if privacy_hint in {"sensitive", "private"} or _contains_any(t, ["合同", "客户资料", "身份证", "手机号", "内部数据", "隐私", "商业机密"], signals, "privacy"):
        profile.privacy_level = PrivacyLevel.SENSITIVE if privacy_hint != "private" else PrivacyLevel.PRIVATE

    # Complexity escalation by length/signals.
    if profile.requires_long_context and profile.complexity in {Complexity.LOW, Complexity.MEDIUM}:
        profile.complexity = Complexity.HIGH
    if len(q) > 1200 and profile.complexity == Complexity.LOW:
        profile.complexity = Complexity.MEDIUM
    if re.search(r"```|traceback|assert |failed|error:", q, re.I):
        profile.requires_coding = True
        profile.category = TaskCategory.DEBUGGING
        profile.complexity = Complexity.HIGH
        signals.append("code_block_or_error")

    if has_tools:
        profile.requires_tool_calling = True
    if profile.requires_web or profile.requires_file_access or profile.requires_image_generation or profile.requires_video_generation:
        profile.requires_tool_calling = True

    if profile.requires_vision:
        profile.hard_constraints.append("vision")
    if profile.requires_tool_calling:
        profile.hard_constraints.append("tool_calling")
    if profile.requires_json_output:
        profile.hard_constraints.append("json")
    if profile.requires_long_context:
        profile.hard_constraints.append("long_context")
    if profile.privacy_level != PrivacyLevel.NORMAL:
        profile.hard_constraints.append("privacy")

    profile.matched_signals = signals
    return profile
