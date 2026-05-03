"""
V106 统一懒加载策略

定义所有组件的懒加载分层：P0（预加载）、P1（预热）、P2（按需）、P3（阻塞/模拟）。

约束：
1. 不调用外部 API。
2. 不真实支付、发送、签署、设备执行。
3. 不改 V90/V92/V100 主闸门。
4. 不让安全规则和人格上下文懒加载。
5. 不允许因为懒加载导致 V95.2 / V96 / V100 / V104.3 / V105 回退。
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import List, Callable, Optional


class LoadPriority(enum.Enum):
    """加载优先级层级"""
    P0_PRELOAD = "preload"   # 启动时立即加载
    P1_WARM = "warm"         # 启动时加载摘要/元数据
    P2_LAZY = "lazy"         # 按需加载完整内容
    P3_BLOCKED = "blocked"   # 阻塞/模拟（离线模式）


@dataclass
class LazyLoadRule:
    """一条懒加载规则"""
    name: str                    # 组件名称
    priority: LoadPriority       # 加载优先级
    description: str             # 描述
    is_security: bool = False    # 是否为安全/人格相关
    requires_external: bool = False  # 是否需要外部 API
    fallback_mock: bool = False  # 是否可降级为 mock
    dependencies: List[str] = field(default_factory=list)  # 前置依赖


# ══════════════════════════════════════════════════
# 所有懒加载规则定义
# ══════════════════════════════════════════════════

RULES = [
    # ── P0 预加载（安全和人格核心，启动即加载） ──
    LazyLoadRule("V90/V92/V100 commit_barrier", LoadPriority.P0_PRELOAD, "commit barrier 主闸门", is_security=True),
    LazyLoadRule("offline_runtime_guard", LoadPriority.P0_PRELOAD, "离线模式守卫", is_security=True),
    LazyLoadRule("mainline_hook", LoadPriority.P0_PRELOAD, "主线 hook", is_security=True),
    LazyLoadRule("AGENTS.md", LoadPriority.P0_PRELOAD, "代理规则", is_security=False),
    LazyLoadRule("IDENTITY.md", LoadPriority.P0_PRELOAD, "身份声明", is_security=False),
    LazyLoadRule("MEMORY.md", LoadPriority.P0_PRELOAD, "长期记忆", is_security=False),
    LazyLoadRule("context_capsule", LoadPriority.P0_PRELOAD, "上下文胶囊", is_security=False, dependencies=["MEMORY.md"]),
    LazyLoadRule("session_handoff", LoadPriority.P0_PRELOAD, "会话交接包", is_security=False),
    LazyLoadRule("CURRENT_RELEASE_INDEX", LoadPriority.P0_PRELOAD, "当前版本索引", is_security=False),
    LazyLoadRule("skill_policy_gate", LoadPriority.P0_PRELOAD, "技能策略门", is_security=True),
    LazyLoadRule("NO_EXTERNAL_API/NO_REAL_*", LoadPriority.P0_PRELOAD, "离线环境变量", is_security=True),

    # ── P1 预热（摘要元数据，快速加载） ──
    LazyLoadRule("skill_trigger_registry.json", LoadPriority.P1_WARM, "技能触发注册表", is_security=False),
    LazyLoadRule("proactive_skill_matcher", LoadPriority.P1_WARM, "主动技能联想器", is_security=False),
    LazyLoadRule("skill_metadata_index", LoadPriority.P1_WARM, "技能元数据索引", is_security=False),
    LazyLoadRule("current_reports_summary", LoadPriority.P1_WARM, "当前报告摘要", is_security=False),
    LazyLoadRule("relationship_memory_summary", LoadPriority.P1_WARM, "关系记忆摘要", is_security=False),
    LazyLoadRule("persona_state_summary", LoadPriority.P1_WARM, "人格状态摘要", is_security=False),

    # ── P2 按需（用户触发时才加载完整内容） ──
    LazyLoadRule("full_SKILL.md", LoadPriority.P2_LAZY, "技能完整文档", is_security=False, fallback_mock=True),
    LazyLoadRule("PDF/DOCX/Excel_processor", LoadPriority.P2_LAZY, "文档处理器", is_security=False, fallback_mock=True),
    LazyLoadRule("Image/Video_processor", LoadPriority.P2_LAZY, "图像/视频处理器", is_security=False, fallback_mock=True),
    LazyLoadRule("GUI/Visual_Agent", LoadPriority.P2_LAZY, "图形界面代理", is_security=False, fallback_mock=True),
    LazyLoadRule("multimodal_index", LoadPriority.P2_LAZY, "多模态索引", is_security=False, fallback_mock=True),
    LazyLoadRule("old_reports", LoadPriority.P2_LAZY, "旧版本报告", is_security=False, fallback_mock=True),
    LazyLoadRule("speculative_modules", LoadPriority.P2_LAZY, "推测/GPU模块", is_security=False, fallback_mock=True),
    LazyLoadRule("connector_factories", LoadPriority.P2_LAZY, "连接器工厂", is_security=False, fallback_mock=True),

    # ── P3 阻塞/模拟（离线模式禁止） ──
    LazyLoadRule("external_API_skills", LoadPriority.P3_BLOCKED, "外部 API 技能", is_security=True, requires_external=True, fallback_mock=True),
    LazyLoadRule("webhook/email/calendar", LoadPriority.P3_BLOCKED, "网络钩子/邮件/日历", is_security=True, requires_external=True, fallback_mock=True),
    LazyLoadRule("cloud_upload", LoadPriority.P3_BLOCKED, "云上传", is_security=True, requires_external=True, fallback_mock=True),
    LazyLoadRule("real_payment/send/device", LoadPriority.P3_BLOCKED, "真实支付/外发/设备", is_security=True, requires_external=True, fallback_mock=True),
    LazyLoadRule("Celery/Redis/PostgreSQL_backend", LoadPriority.P3_BLOCKED, "Celery/Redis/PostgreSQL 真实后端", is_security=False, requires_external=True, fallback_mock=True),
]

# 快速查找
_RULES_BY_NAME = {r.name: r for r in RULES}


def get_rule(name: str) -> Optional[LazyLoadRule]:
    """获取指定组件的懒加载规则。"""
    return _RULES_BY_NAME.get(name)


def get_rules_by_priority(priority: LoadPriority) -> List[LazyLoadRule]:
    """获取指定优先级的所有规则。"""
    return [r for r in RULES if r.priority == priority]


def get_p0_names() -> List[str]:
    """获取 P0 预加载组件名称列表。"""
    return [r.name for r in RULES if r.priority == LoadPriority.P0_PRELOAD]


def get_p2_names() -> List[str]:
    """获取 P2 按需加载组件名称列表。"""
    return [r.name for r in RULES if r.priority == LoadPriority.P2_LAZY]


def is_security_related(name: str) -> bool:
    """判断组件是否与安全/人格相关（不应懒加载）。"""
    rule = _RULES_BY_NAME.get(name)
    return rule.is_security if rule else False


def should_block_in_offline(name: str) -> bool:
    """在离线模式下是否应阻塞该组件。"""
    rule = _RULES_BY_NAME.get(name)
    return rule.requires_external if rule else False


def policy_summary() -> str:
    """生成策略摘要文本。"""
    lines = ["## V106 统一懒加载策略", ""]
    for priority in [LoadPriority.P0_PRELOAD, LoadPriority.P1_WARM, LoadPriority.P2_LAZY, LoadPriority.P3_BLOCKED]:
        rules = get_rules_by_priority(priority)
        lines.append(f"{'🟢' if priority == LoadPriority.P0_PRELOAD else '🟡' if priority == LoadPriority.P1_WARM else '🔵' if priority == LoadPriority.P2_LAZY else '🔴'} {priority.value} ({len(rules)} 个组件)")
        for r in rules:
            tag = ""
            if r.is_security: tag += " 🔒"
            if r.requires_external: tag += " 🌐"
            if r.fallback_mock: tag += " 🎭"
            lines.append(f"  - {r.name}{tag}: {r.description}")
        lines.append("")
    return "\n".join(lines)
