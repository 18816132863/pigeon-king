"""Action semantics for the embodied-pending-access state.

This module turns every intended operation into one of the semantic classes
needed by the report target:
- observe/reason/generate/simulate/prepare are allowed in the pending state.
- external send/payment/signature/physical actuation/destructive commits are
  stopped before any real-world side effect.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


class SemanticClass(str, Enum):
    OBSERVE = "observe"
    REASON = "reason"
    GENERATE = "generate"
    SIMULATE = "simulate"
    PREPARE = "prepare"
    EXTERNAL_SEND = "external_send"
    PAYMENT = "payment"
    SIGNATURE = "signature"
    PHYSICAL_ACTUATION = "physical_actuation"
    IDENTITY_COMMIT = "identity_commit"
    DESTRUCTIVE = "destructive"
    UNKNOWN = "unknown"


ALLOWED_PENDING_CLASSES = {
    SemanticClass.OBSERVE,
    SemanticClass.REASON,
    SemanticClass.GENERATE,
    SemanticClass.SIMULATE,
    SemanticClass.PREPARE,
}

COMMIT_CLASSES = {
    SemanticClass.EXTERNAL_SEND,
    SemanticClass.PAYMENT,
    SemanticClass.SIGNATURE,
    SemanticClass.PHYSICAL_ACTUATION,
    SemanticClass.IDENTITY_COMMIT,
    SemanticClass.DESTRUCTIVE,
}

HARD_STOP_CLASSES = {
    SemanticClass.PAYMENT,
    SemanticClass.SIGNATURE,
    SemanticClass.PHYSICAL_ACTUATION,
    SemanticClass.IDENTITY_COMMIT,
    SemanticClass.DESTRUCTIVE,
}

_KEYWORD_RULES: Sequence[tuple[SemanticClass, Sequence[str]]] = (
    (SemanticClass.PAYMENT, (
        "pay", "payment", "purchase", "buy", "order", "checkout", "transfer", "wire",
        "invoice_pay", "alipay", "wechat_pay", "stripe", "refund", "topup", "recharge",
        "付款", "支付", "下单", "购买", "买入", "转账", "打款", "充值", "扣款", "结算",
        "退款", "订购", "采购", "花钱", "收款", "开票付款",
    )),
    (SemanticClass.SIGNATURE, (
        "sign", "signature", "contract", "agreement", "accept_terms", "commit_contract",
        "签约", "签署", "合同", "协议", "承诺书", "盖章", "电子签", "确认协议",
    )),
    (SemanticClass.PHYSICAL_ACTUATION, (
        "move", "grab", "pick", "place", "open_door", "unlock", "lock", "robot", "actuator",
        "motor", "vehicle", "drive", "start_device", "stop_device", "power_on", "power_off",
        "开门", "关门", "门锁", "解锁", "上锁", "移动", "抓取", "拿起", "放下", "机器人",
        "机械臂", "电机", "车控", "开车", "设备启停", "启动设备", "关闭设备", "物理执行",
    )),
    (SemanticClass.EXTERNAL_SEND, (
        "send", "email", "sms", "message", "post", "publish", "notify", "call", "webhook",
        "external_api", "public", "outbound", "mail", "发送", "邮件", "短信", "消息", "通知",
        "外发", "发布", "公开", "发帖", "打电话", "对外", "外部api", "推送",
    )),
    (SemanticClass.IDENTITY_COMMIT, (
        "represent", "identity", "authorize_as", "promise", "guarantee", "represent_user",
        "代表我", "以我名义", "身份承诺", "承诺", "保证", "授权代表",
    )),
    (SemanticClass.DESTRUCTIVE, (
        "delete", "drop", "wipe", "reset", "destroy", "remove", "archive_destructive", "revoke",
        "删除", "清空", "销毁", "重置", "注销", "撤销", "移除", "格式化",
    )),
    (SemanticClass.SIMULATE, (
        "simulate", "simulation", "sandbox", "mock", "dry_run", "replay", "shadow", "digital_twin",
        "仿真", "模拟", "沙箱", "影子", "回放", "干跑", "数字孪生", "mock",
    )),
    (SemanticClass.PREPARE, (
        "draft", "prepare", "preview", "cart", "plan_only", "candidate", "proposal", "checklist",
        "草稿", "准备", "预览", "待执行", "购物车", "清单", "候选", "方案", "只生成",
    )),
    (SemanticClass.GENERATE, (
        "generate", "create_draft", "write", "compose", "render", "produce", "make_content",
        "生成", "撰写", "写", "制作内容", "出方案", "起草", "整理文案",
    )),
    (SemanticClass.OBSERVE, (
        "read", "search", "list", "query", "inspect", "scan", "fetch", "observe", "get_",
        "读取", "查询", "搜索", "查看", "列出", "扫描", "观察", "获取",
    )),
    (SemanticClass.REASON, (
        "reason", "analyze", "judge", "decide", "classify", "summarize", "evaluate", "rank",
        "分析", "判断", "决策", "分类", "总结", "评估", "排序", "推理",
    )),
)

@dataclass(frozen=True)
class ActionSemanticDecision:
    semantic_class: str
    risk_level: str
    is_commit_action: bool
    hard_stop: bool
    allowed_in_pending_access_state: bool
    matched_terms: List[str]
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Mapping):
        return " ".join(_flatten_text(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(_flatten_text(v) for v in value)
    return str(value)


def _collect_action_text(action: Mapping[str, Any]) -> str:
    fields = [
        "semantic_class", "action_type", "capability", "capability_name", "op_name", "name",
        "route_id", "summary", "description", "intent", "tool", "endpoint", "scopes", "payload",
    ]
    parts = []
    for field in fields:
        if field in action:
            parts.append(_flatten_text(action[field]))
    if not parts:
        parts.append(_flatten_text(action))
    return " ".join(parts).lower()


def _risk_for_class(cls: SemanticClass) -> str:
    if cls in {SemanticClass.PAYMENT, SemanticClass.SIGNATURE, SemanticClass.PHYSICAL_ACTUATION, SemanticClass.IDENTITY_COMMIT, SemanticClass.DESTRUCTIVE}:
        return "L4"
    if cls == SemanticClass.EXTERNAL_SEND:
        return "L3"
    if cls in {SemanticClass.PREPARE, SemanticClass.GENERATE, SemanticClass.SIMULATE}:
        return "L2"
    if cls in {SemanticClass.OBSERVE, SemanticClass.REASON}:
        return "L1"
    return "L2"


def classify_action_semantics(action: Mapping[str, Any] | None) -> ActionSemanticDecision:
    action = action or {}
    explicit = action.get("semantic_class") or action.get("action_semantic")
    if explicit:
        try:
            cls = SemanticClass(str(explicit))
            matched_terms = [str(explicit)]
        except ValueError:
            cls = SemanticClass.UNKNOWN
            matched_terms = [str(explicit)]
    else:
        text = _collect_action_text(action)
        cls = SemanticClass.UNKNOWN
        matched_terms: List[str] = []
        for candidate, terms in _KEYWORD_RULES:
            hits = [term for term in terms if term.lower() in text]
            if hits:
                cls = candidate
                matched_terms = hits[:8]
                break
        # explicit flags override low-risk words hidden in names
        payload = action.get("payload", {}) if isinstance(action.get("payload", {}), Mapping) else {}
        flag_source = {**{k: v for k, v in action.items() if isinstance(k, str)}, **payload}
        if flag_source.get("payment") or flag_source.get("spend_money") or flag_source.get("financial_commit"):
            cls, matched_terms = SemanticClass.PAYMENT, ["financial_commit_flag"]
        elif flag_source.get("physical_actuation") or flag_source.get("device_side_effect"):
            cls, matched_terms = SemanticClass.PHYSICAL_ACTUATION, ["physical_actuation_flag"]
        elif flag_source.get("destructive") or flag_source.get("irreversible"):
            cls, matched_terms = SemanticClass.DESTRUCTIVE, ["irreversible_flag"]
        elif flag_source.get("side_effecting") and flag_source.get("recipient"):
            cls, matched_terms = SemanticClass.EXTERNAL_SEND, ["side_effecting_recipient_flag"]

    is_commit = cls in COMMIT_CLASSES
    hard_stop = cls in HARD_STOP_CLASSES
    allowed = cls in ALLOWED_PENDING_CLASSES
    if is_commit:
        reason = "commit_action_must_stop_before_real_world_side_effect"
    elif allowed:
        reason = "pending_access_state_allows_non_commit_action"
    else:
        reason = "unknown_or_unclassified_action_requires_review"
        allowed = False
    return ActionSemanticDecision(
        semantic_class=cls.value,
        risk_level=_risk_for_class(cls),
        is_commit_action=is_commit,
        hard_stop=hard_stop,
        allowed_in_pending_access_state=allowed,
        matched_terms=matched_terms,
        reason=reason,
    )


def is_commit_action(action: Mapping[str, Any] | None) -> bool:
    return classify_action_semantics(action).is_commit_action


def default_action_catalog() -> List[Dict[str, Any]]:
    """100+ high-value action semantics used by readiness gates and docs."""
    base = []
    groups = {
        SemanticClass.OBSERVE: ["read_file", "query_calendar", "search_web", "list_tasks", "inspect_screen", "read_sensor_replay", "query_contact", "read_email", "scan_inventory", "get_location_status", "read_device_setting", "query_order_status", "list_recent_messages", "read_knowledge_base", "fetch_document", "read_log", "inspect_photo", "query_note"],
        SemanticClass.REASON: ["analyze_contract", "judge_priority", "rank_options", "summarize_report", "classify_risk", "evaluate_supplier", "decide_next_step", "compare_prices", "diagnose_failure", "estimate_profit", "review_plan", "detect_conflict", "score_capability", "infer_user_preference", "triage_inbox", "audit_trace", "explain_result"],
        SemanticClass.GENERATE: ["write_draft", "generate_report", "compose_script", "create_plan", "make_prompt", "render_markdown", "generate_test_case", "create_checklist", "draft_email", "draft_message", "generate_image_prompt", "write_code_patch", "create_meeting_notes", "make_table", "prepare_contract_summary"],
        SemanticClass.SIMULATE: ["dry_run_action", "mock_api_call", "sandbox_install", "replay_trace", "shadow_execute", "simulate_calendar_insert", "simulate_payment", "simulate_robot_move", "digital_twin_update", "counterfactual_review", "mock_connector_call", "simulate_email_send", "simulate_file_delete", "simulate_device_action"],
        SemanticClass.PREPARE: ["prepare_cart", "prepare_email_draft", "prepare_calendar_event", "prepare_purchase_order", "prepare_robot_trajectory", "prepare_api_payload", "prepare_call_script", "prepare_upload", "prepare_release", "prepare_backup", "prepare_rollback", "prepare_approval_pack", "prepare_contract_draft"],
        SemanticClass.EXTERNAL_SEND: ["send_email", "send_sms", "publish_post", "call_phone", "notify_external", "webhook_post", "submit_form", "upload_public_file", "resend_message", "forward_email"],
        SemanticClass.PAYMENT: ["pay_invoice", "checkout_order", "transfer_money", "recharge_account", "buy_product", "refund_payment", "subscribe_service", "purchase_api_credit", "settle_bill", "place_paid_order"],
        SemanticClass.SIGNATURE: ["sign_contract", "accept_terms", "sign_agreement", "seal_document", "commit_contract", "approve_legal_commitment", "confirm_identity_authorization"],
        SemanticClass.PHYSICAL_ACTUATION: ["unlock_door", "start_device", "stop_device", "move_robot", "grab_object", "drive_vehicle", "open_valve", "power_off_machine", "robot_handoff", "physical_delivery"],
        SemanticClass.IDENTITY_COMMIT: ["represent_user", "promise_delivery", "guarantee_outcome", "authorize_as_user", "make_public_commitment"],
        SemanticClass.DESTRUCTIVE: ["delete_file", "wipe_data", "reset_device", "drop_database", "revoke_access", "cancel_account", "remove_contact", "destroy_backup"],
    }
    for cls, names in groups.items():
        for name in names:
            base.append({
                "name": name,
                "semantic_class": cls.value,
                "risk_level": _risk_for_class(cls),
                "pending_policy": "allow" if cls in ALLOWED_PENDING_CLASSES else "stop_at_commit_barrier",
            })
    return base
