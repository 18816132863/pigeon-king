"""
V26.1 — Universal Task Contract Builder

构建器：分析用户输入 → 提取意图 → 创建来源契约 → 创建动作契约 → 生成任务契约
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .schemas import (
    ActionContract,
    CompletionCriteria,
    ExecutionPolicy,
    IdempotencyKey,
    IntentType,
    RiskLevel,
    SourceContract,
    StopCondition,
    ToolRole,
    UniversalTaskContract,
)

# ---------------------------------------------------------------
# Intent keywords
# ---------------------------------------------------------------
CREATE_KEYWORDS = [
    "创建", "设置", "写上", "全部写上", "加到", "生成", "安排", "设提醒",
    "设闹钟", "加日历", "直接", "跑", "覆盖", "替换", "添加", "新增",
]
SEARCH_KEYWORDS = [
    "搜索", "找", "查找", "查询", "检索", "搜", "查",
]
READ_KEYWORDS = [
    "看", "读", "查看", "浏览", "打开",
]
UPDATE_KEYWORDS = [
    "修改", "更新", "编辑", "改",
]
DELETE_KEYWORDS = [
    "删", "删除", "清除", "清空",
]
EXECUTE_KEYWORDS = [
    "执行", "运行", "启动", "开始",
]
SEND_KEYWORDS = [
    "发送", "发", "邮", "转发",
]
RECOVER_KEYWORDS = [
    "恢复", "恢复", "还原",
]
SUMMARIZE_KEYWORDS = [
    "汇总", "总结", "整理", "归纳", "提取",
]
EXTRACT_KEYWORDS = [
    "抽取", "提取", "摘取", "提取关键",
]


def detect_intent(user_input: str) -> IntentType:
    """分析用户输入，检测意图"""
    if not user_input:
        return IntentType.SEARCH

    text = user_input.lower()

    # 优先级：创建 > 删除 > 更新 > 发送 > 执行 > 恢复 > 提取 > 汇总 > 读取 > 搜索

    for kw in CREATE_KEYWORDS:
        if kw in text:
            return IntentType.CREATE

    for kw in DELETE_KEYWORDS:
        if kw in text:
            return IntentType.DELETE

    for kw in UPDATE_KEYWORDS:
        if kw in text:
            return IntentType.UPDATE

    for kw in SEND_KEYWORDS:
        if kw in text:
            return IntentType.SEND

    for kw in EXECUTE_KEYWORDS:
        if kw in text:
            return IntentType.EXECUTE

    for kw in RECOVER_KEYWORDS:
        if kw in text:
            return IntentType.RECOVER

    for kw in EXTRACT_KEYWORDS:
        if kw in text:
            return IntentType.EXTRACT

    for kw in SUMMARIZE_KEYWORDS:
        if kw in text:
            return IntentType.SUMMARIZE

    for kw in READ_KEYWORDS:
        if kw in text:
            return IntentType.READ

    for kw in SEARCH_KEYWORDS:
        if kw in text:
            return IntentType.SEARCH

    return IntentType.SEARCH  # 默认


def detect_source(user_input: str, default_source: str = "") -> Tuple[str, str, List[str], str, str, str, List[str]]:
    """
    分析用户输入，提取来源信息

    返回: (primary_source, title_hint, keywords, date_hint, location_hint, person_hint, exclude_keywords)
    """
    text = user_input.lower() if user_input else ""

    # 检测来源
    sources = []
    if "备忘录" in text or "笔记" in text:
        sources.append("notes")
    if "日历" in text or "日程" in text:
        sources.append("calendar")
    if "闹钟" in text:
        sources.append("alarm")
    if "邮件" in text or "邮箱" in text or "gmail" in text:
        sources.append("gmail")
    if "文件" in text:
        sources.append("file")
    if "手机" in text or "设备" in text:
        sources.append("device")
    if "网页" in text:
        sources.append("web")

    primary_source = sources[0] if sources else default_source or "user_input"

    # 提取关键词：去除常见停用词
    stop_words = {"的", "了", "在", "是", "有", "和", "与", "就", "都", "而",
                  "及", "把", "被", "让", "给", "对", "从", "到", "去", "用",
                  "以", "为", "能", "要", "会", "可", "以", "这", "那", "哪",
                  "你", "我", "他", "她", "它", "们", "个", "些", "把", "吧",
                  "吗", "呢", "啊", "哦", "嗯", "哈"}

    words = [w for w in re.findall(r"[a-zA-Z0-9\u4e00-\u9fff]+", text) if w not in stop_words and len(w) > 1]

    # 提取日期线索
    date_hint = ""
    date_patterns = [
        (r"(五一|5月1|5月2|5月3|5月4)", "0501"),
        (r"(明天|今日|今天|今晚)", ""),
        (r"(\d{1,2})月(\d{1,2})", ""),
    ]
    for pattern, default in date_patterns:
        m = re.search(pattern, text)
        if m:
            date_hint = m.group(0)
            break

    # 提取地点线索
    location_hint = ""
    location_keywords = ["平遥", "太原", "虹桥", "上海", "济南", "合肥", "河南",
                         "邯郸", "河北", "山东"]
    for loc in location_keywords:
        if loc in text:
            location_hint = loc
            break

    # 提取人物线索
    person_hint = ""
    person_keywords = ["姑姑", "爸爸", "妈妈", "老爸", "老妈", "家人"]
    for person in person_keywords:
        if person in text:
            person_hint = person
            break

    # 排除词
    exclude_keywords = []
    if "不要" in text or "不" in text:
        # 简单排除检测
        not_patterns = re.findall(r"不[要想]\w+", text)
        exclude_keywords = [w for w in not_patterns if w not in stop_words]

    # 标题线索：引号中的内容或"那个/这个"后的词
    title_hint = ""
    quote_matches = re.findall(r"[""「『]([^""」』]+)[""」』]", text)
    if quote_matches:
        title_hint = quote_matches[0]

    return primary_source, title_hint, words, date_hint, location_hint, person_hint, exclude_keywords


def detect_actions(source_name: str, intent: IntentType) -> List[str]:
    """根据来源和意图，确定动作"""
    actions = []
    if source_name == "notes":
        if intent in [IntentType.CREATE, IntentType.SCHEDULE, IntentType.REMIND]:
            actions.append("create_note")
        elif intent == IntentType.SEARCH:
            actions.append("search_notes")
        elif intent == IntentType.UPDATE:
            actions.append("modify_note")
        elif intent == IntentType.DELETE:
            actions.append("delete_note")
        else:
            actions.append("search_notes")
    elif source_name == "calendar":
        if intent in [IntentType.CREATE, IntentType.SCHEDULE]:
            actions.append("create_calendar_event")
        elif intent == IntentType.SEARCH:
            actions.append("search_calendar_event")
        elif intent == IntentType.UPDATE:
            actions.append("modify_calendar_event")
        elif intent == IntentType.DELETE:
            actions.append("delete_calendar_event")
        else:
            actions.append("search_calendar_event")
    elif source_name == "alarm":
        if intent in [IntentType.CREATE, IntentType.REMIND]:
            actions.append("create_alarm")
        elif intent == IntentType.SEARCH:
            actions.append("search_alarm")
        elif intent == IntentType.DELETE:
            actions.append("delete_alarm")
        elif intent == IntentType.UPDATE:
            actions.append("modify_alarm")
        else:
            actions.append("search_alarm")
    elif source_name == "gmail":
        if intent == IntentType.SEND:
            actions.extend(["draft_email", "send_email"])
        elif intent == IntentType.DRAFT:
            actions.append("draft_email")
        else:
            actions.append("read_email")
    elif source_name == "file":
        actions.append("read_file")
    elif source_name == "device":
        actions.append("device_action")
    else:
        actions.append("search")

    return actions


def build_action_contract(actions: List[str], intent: IntentType) -> ActionContract:
    """构建动作契约"""
    tool_roles = {}
    for action in actions:
        if action.startswith("search") or action.startswith("read"):
            tool_roles[action] = ToolRole.SOURCE_SEARCH
        elif action.startswith("create") or action.startswith("modify"):
            tool_roles[action] = ToolRole.PRIMARY_ACTION
        elif action.startswith("delete"):
            tool_roles[action] = ToolRole.PRIMARY_ACTION
        elif action == "draft_email":
            tool_roles[action] = ToolRole.PRIMARY_ACTION
        elif action == "send_email":
            tool_roles[action] = ToolRole.PRIMARY_ACTION
        elif action == "device_action":
            tool_roles[action] = ToolRole.PRIMARY_ACTION
        else:
            tool_roles[action] = ToolRole.VALIDATION_CHECK

    return ActionContract(actions=actions, tool_roles=tool_roles)


def build_idempotency_key(source_name: str, intent: IntentType,
                          title: str = "", date_hint: str = "",
                          target: str = "") -> IdempotencyKey:
    """构建幂等键"""
    return IdempotencyKey(
        source_id=source_name,
        action_type=intent.value,
        date=date_hint,
        time=datetime.now().strftime("%H%M"),
        title=title,
        target=target,
    )


def determine_execution_policy(intent: IntentType, risk: RiskLevel) -> ExecutionPolicy:
    """确定执行策略"""
    if risk in [RiskLevel.L4_HIGH, RiskLevel.L5_RITICAL]:
        return ExecutionPolicy.BLOCKED
    if intent == IntentType.SEND:
        return ExecutionPolicy.APPROVAL_REQUIRED
    if intent == IntentType.DELETE:
        return ExecutionPolicy.APPROVAL_REQUIRED
    if intent == IntentType.EXECUTE:
        return ExecutionPolicy.APPROVAL_REQUIRED
    if risk == RiskLevel.L3_REVERSIBLE:
        return ExecutionPolicy.DRY_RUN
    return ExecutionPolicy.REAL


def determine_risk(actions: List[str], intent: IntentType) -> RiskLevel:
    """确定风险等级"""
    if intent == IntentType.SEND:
        return RiskLevel.L3_REVERSIBLE
    if intent == IntentType.DELETE:
        return RiskLevel.L3_REVERSIBLE
    if any("delete" in a or "send" in a for a in actions):
        return RiskLevel.L3_REVERSIBLE
    if intent in [IntentType.CREATE, IntentType.UPDATE]:
        return RiskLevel.L2_REVERSIBLE
    return RiskLevel.L1_LOW


def determine_stop_conditions(intent: IntentType, actions: List[str]) -> List[StopCondition]:
    """确定停止条件"""
    conditions = []
    if intent in [IntentType.CREATE, IntentType.DELETE, IntentType.UPDATE]:
        if not any(a.startswith("search") or a.startswith("read") for a in actions):
            conditions.append(StopCondition.NO_IDEMPOTENCY_KEY)
    if intent == IntentType.SEND:
        conditions.append(StopCondition.HIGH_RISK_NO_APPROVAL)
    return conditions


# ---------------------------------------------------------------
# 主构建器
# ---------------------------------------------------------------


class ContractBuilder:
    """通用任务契约构建器"""

    @staticmethod
    def build(user_input: str, default_source: str = "") -> UniversalTaskContract:
        """
        从用户输入构建通用任务契约

        Args:
            user_input: 用户输入（自然语言）
            default_source: 默认来源（如果无法从输入推断）

        Returns:
            UniversalTaskContract: 通用任务契约
        """
        # 1. 检测意图
        intent = detect_intent(user_input)

        # 2. 检测来源
        primary_source, title_hint, keywords, date_hint, location_hint, person_hint, exclude_keywords = \
            detect_source(user_input, default_source)

        # 3. 构建来源契约
        source = SourceContract(
            primary_source=primary_source,
            keywords=keywords,
            title_hint=title_hint,
            date_hint=date_hint,
            location_hint=location_hint,
            person_hint=person_hint,
            exclude_keywords=exclude_keywords,
        )

        # 4. 检测动作
        actions = detect_actions(primary_source, intent)

        # 5. 构建动作契约
        action = build_action_contract(actions, intent)

        # 6. 确定风险和策略
        risk = determine_risk(actions, intent)
        execution_policy = determine_execution_policy(intent, risk)

        # 7. 构建幂等键
        idempotency_key = build_idempotency_key(primary_source, intent, title_hint, date_hint)

        # 8. 确定停止条件
        stop_conditions = determine_stop_conditions(intent, actions)

        # 9. 完成标准
        completion_criteria = CompletionCriteria(
            must_have=[f"{intent.value}_success"],
            evidence_required=[primary_source] if primary_source != "user_input" else [],
            min_matches=1,
        )

        # 10. 生成契约
        contract = UniversalTaskContract(
            goal=user_input,
            intent=intent,
            source=source,
            action=action,
            risk=risk,
            execution_policy=execution_policy,
            idempotency_key=idempotency_key,
            checkpoint_id=f"ck_{intent.value}_{primary_source[:3]}_{datetime.now().strftime('%H%M%S')}",
            stop_conditions=stop_conditions,
            completion_criteria=completion_criteria,
            timeout_policy="async_job" if intent in [IntentType.CREATE, IntentType.DELETE,
            IntentType.SCHEDULE, IntentType.REMIND, IntentType.SEND] else "sync",
            multi_source_merge=False,
        )

        return contract
