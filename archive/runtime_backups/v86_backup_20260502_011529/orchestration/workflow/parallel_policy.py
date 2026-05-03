"""
V86 Controlled Parallel Policy
受控并行策略：低风险并行，高风险串行/审批/截断。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional

try:
    from orchestration.workflow.workflow_registry import WorkflowStep
except Exception:  # pragma: no cover
    WorkflowStep = Any  # type: ignore


class ParallelClass(Enum):
    SAFE_PARALLEL = "safe_parallel"
    SERIAL_REQUIRED = "serial_required"
    APPROVAL_REQUIRED = "approval_required"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ParallelDecision:
    step_id: str
    parallel_class: ParallelClass
    reason: str
    matched_rules: List[str] = field(default_factory=list)

    @property
    def can_run_parallel(self) -> bool:
        return self.parallel_class == ParallelClass.SAFE_PARALLEL

    @property
    def must_run_serial(self) -> bool:
        return self.parallel_class == ParallelClass.SERIAL_REQUIRED

    @property
    def requires_approval(self) -> bool:
        return self.parallel_class == ParallelClass.APPROVAL_REQUIRED

    @property
    def is_blocked(self) -> bool:
        return self.parallel_class == ParallelClass.BLOCKED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "parallel_class": self.parallel_class.value,
            "reason": self.reason,
            "matched_rules": list(self.matched_rules),
        }


class ParallelPolicy:
    """
    V86 受控并行策略。

    原则：
    - 分析、检索、生成、仿真、验证、草稿、mock/test/noop 可以并行。
    - 端侧/真实账户/日历联系人真实写入只能串行。
    - 外发、支付、签约、删除、物理致动默认进入提交屏障。
    """

    SAFE_ACTION_KEYWORDS = {
        "analyze", "analysis", "reason", "think", "plan", "search", "retrieve",
        "read", "fetch", "load", "summarize", "summary", "classify", "rank",
        "generate", "draft", "compose", "rewrite", "format", "simulate", "mock",
        "dry_run", "validate", "verify", "check", "inspect", "score", "eval",
        "test", "noop", "initialize", "prepare", "finalize", "render", "preview",
        "extract", "transform", "build_report",
    }

    SERIAL_ACTION_KEYWORDS = {
        "calendar", "contact", "phone", "mobile", "device", "end_side", "endside",
        "alarm", "reminder", "local_app", "os_action", "credential", "account_write",
        "file_write", "write_file", "move_file", "rename_file", "upload", "download_commit",
    }

    COMMIT_ACTION_KEYWORDS = {
        "pay", "payment", "checkout", "purchase", "order_submit", "place_order",
        "transfer", "withdraw", "refund", "invoice", "contract", "sign", "signature",
        "external_send", "send_email", "email_send", "send_message", "sms_send",
        "wechat_send", "publish", "post_public", "public_post", "submit_form",
        "delete", "remove", "destroy", "drop", "truncate", "door", "lock", "unlock",
        "robot", "actuate", "physical", "motor", "vehicle", "turn_on", "turn_off",
        "start_device", "stop_device",
    }

    SAFE_SIDE_EFFECT_TYPES = {"none", "observe", "read", "reason", "generate", "simulate", "prepare", "draft", "validate"}
    SERIAL_SIDE_EFFECT_TYPES = {"internal_write", "local_write", "calendar_write", "contact_write", "device_prepare"}
    COMMIT_SIDE_EFFECT_TYPES = {"external_send", "payment", "contract", "signature", "delete", "physical", "device_commit"}

    BLOCKING_CAPABILITY_KEYWORDS = {
        "payment", "pay", "transfer", "contract", "signature", "physical", "actuator",
        "door_lock", "vehicle", "public_publish", "external_send", "delete_external",
    }

    SERIAL_CAPABILITY_KEYWORDS = {
        "end_side", "phone", "mobile", "calendar_write", "contact_write", "device_write",
        "account_write", "local_os", "credential_use",
    }

    def classify(self, step: WorkflowStep, control_decision: Optional[Dict[str, Any]] = None) -> ParallelDecision:
        control_decision = control_decision or {}
        text = self._normalized_text(step)
        caps = [str(c).lower() for c in getattr(step, "required_capabilities", []) or []]
        params = getattr(step, "params", {}) or {}
        step_id = getattr(step, "step_id", "unknown")

        blocked_caps = {str(c).lower() for c in control_decision.get("blocked_capabilities", []) or []}
        if any(c in blocked_caps for c in caps):
            return ParallelDecision(step_id, ParallelClass.BLOCKED, "capability blocked by control decision", ["blocked_capabilities"])

        forced = params.get("parallel_class") or params.get("force_parallel_class")
        if forced:
            decision = self._decision_from_forced_value(step_id, str(forced))
            if decision:
                return decision

        if params.get("parallel") is False or params.get("serial_required") is True:
            return ParallelDecision(step_id, ParallelClass.SERIAL_REQUIRED, "step explicitly marked serial", ["params.serial_required"])

        if params.get("blocked") is True:
            return ParallelDecision(step_id, ParallelClass.BLOCKED, "step explicitly blocked", ["params.blocked"])

        if params.get("requires_approval") is True:
            return ParallelDecision(step_id, ParallelClass.APPROVAL_REQUIRED, "step explicitly requires approval", ["params.requires_approval"])

        side_effect = str(params.get("side_effect_type", "")).lower().strip()
        if side_effect in self.COMMIT_SIDE_EFFECT_TYPES:
            return ParallelDecision(step_id, ParallelClass.APPROVAL_REQUIRED, f"commit side effect: {side_effect}", ["side_effect_type.commit"])
        if side_effect in self.SERIAL_SIDE_EFFECT_TYPES:
            return ParallelDecision(step_id, ParallelClass.SERIAL_REQUIRED, f"serial side effect: {side_effect}", ["side_effect_type.serial"])
        if side_effect in self.SAFE_SIDE_EFFECT_TYPES:
            return ParallelDecision(step_id, ParallelClass.SAFE_PARALLEL, f"safe side effect: {side_effect}", ["side_effect_type.safe"])

        if getattr(step, "is_high_risk", False):
            return ParallelDecision(step_id, ParallelClass.APPROVAL_REQUIRED, "step marked high risk", ["step.is_high_risk"])

        if self._contains_any(caps, self.BLOCKING_CAPABILITY_KEYWORDS) or self._contains_any([text], self.COMMIT_ACTION_KEYWORDS):
            return ParallelDecision(step_id, ParallelClass.APPROVAL_REQUIRED, "commit/high-impact action requires approval barrier", ["commit_keyword"])

        if self._contains_any(caps, self.SERIAL_CAPABILITY_KEYWORDS) or self._contains_any([text], self.SERIAL_ACTION_KEYWORDS):
            return ParallelDecision(step_id, ParallelClass.SERIAL_REQUIRED, "real-world/local-side action must use serial lane", ["serial_keyword"])

        if self._contains_any([text], self.SAFE_ACTION_KEYWORDS):
            return ParallelDecision(step_id, ParallelClass.SAFE_PARALLEL, "safe low-risk action", ["safe_keyword"])

        return ParallelDecision(step_id, ParallelClass.SAFE_PARALLEL, "default safe by absence of side-effect markers", ["default_compatible"])

    def _normalized_text(self, step: WorkflowStep) -> str:
        parts: List[str] = []
        for attr in ("action", "name", "description", "step_id"):
            value = getattr(step, attr, "")
            if value:
                parts.append(str(value))
        for cap in getattr(step, "required_capabilities", []) or []:
            parts.append(str(cap))
        params = getattr(step, "params", {}) or {}
        for key in ("tool", "operation", "intent", "side_effect_type"):
            if key in params:
                parts.append(str(params[key]))
        return " ".join(parts).lower().replace("-", "_").replace("/", "_")

    def _contains_any(self, values: Iterable[str], keywords: Iterable[str]) -> bool:
        values = [v.lower() for v in values]
        return any(keyword in value for value in values for keyword in keywords)

    def _decision_from_forced_value(self, step_id: str, value: str) -> Optional[ParallelDecision]:
        normalized = value.strip().lower()
        aliases = {
            "safe": ParallelClass.SAFE_PARALLEL,
            "safe_parallel": ParallelClass.SAFE_PARALLEL,
            "parallel": ParallelClass.SAFE_PARALLEL,
            "serial": ParallelClass.SERIAL_REQUIRED,
            "serial_required": ParallelClass.SERIAL_REQUIRED,
            "approval": ParallelClass.APPROVAL_REQUIRED,
            "approval_required": ParallelClass.APPROVAL_REQUIRED,
            "blocked": ParallelClass.BLOCKED,
            "block": ParallelClass.BLOCKED,
        }
        klass = aliases.get(normalized)
        if not klass:
            return None
        return ParallelDecision(step_id, klass, f"forced parallel class: {normalized}", ["params.force_parallel_class"])
