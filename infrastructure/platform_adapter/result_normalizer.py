"""
平台结果归一化 - V11.0
将不同平台/端侧工具的原始结果统一映射为标准状态。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


class NormalizedStatus:
    COMPLETED = "completed"
    QUEUED_FOR_DELIVERY = "queued_for_delivery"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RESULT_UNCERTAIN = "result_uncertain"
    AUTH_REQUIRED = "auth_required"
    FALLBACK_USED = "fallback_used"


@dataclass
class NormalizedResult:
    status: str
    error_code: Optional[str] = None
    should_retry: bool = False
    result_uncertain: bool = False


def normalize_result(raw_result: Any, capability: str, op_name: str) -> NormalizedResult:
    from .error_codes import (
        PLATFORM_TIMEOUT,
        PLATFORM_RESULT_UNCERTAIN,
        PLATFORM_AUTH_REQUIRED,
        PLATFORM_PERMISSION_DENIED,
        PLATFORM_NOT_CONNECTED,
        PLATFORM_NOT_AVAILABLE,
        PLATFORM_BAD_PARAMS,
        PLATFORM_EXECUTION_FAILED,
        PLATFORM_FALLBACK_USED,
    )

    if raw_result is None:
        return NormalizedResult(NormalizedStatus.FAILED, PLATFORM_NOT_AVAILABLE, True, False)

    if isinstance(raw_result, dict):
        status = str(raw_result.get("status", "")).lower()
        error_msg = str(raw_result.get("error") or raw_result.get("message") or raw_result.get("desc") or "")
        code = raw_result.get("code")
        success = raw_result.get("success")

        if status in {"queued", "queued_for_delivery"} or raw_result.get("queued") is True:
            return NormalizedResult(NormalizedStatus.QUEUED_FOR_DELIVERY, PLATFORM_FALLBACK_USED, False, False)

        if success is True or status in {"ok", "success", "completed"}:
            return NormalizedResult(NormalizedStatus.COMPLETED, None, False, False)

        if status in {"timeout"} or "timeout" in error_msg.lower() or "超时" in error_msg:
            return NormalizedResult(NormalizedStatus.TIMEOUT, PLATFORM_TIMEOUT, False, True)

        if status in {"auth_required", "unauthorized"} or "authcode" in error_msg.lower() or "授权" in error_msg:
            return NormalizedResult(NormalizedStatus.AUTH_REQUIRED, PLATFORM_AUTH_REQUIRED, False, False)

        if "permission" in error_msg.lower() or "权限" in error_msg:
            return NormalizedResult(NormalizedStatus.FAILED, PLATFORM_PERMISSION_DENIED, False, False)

        if "not connected" in error_msg.lower() or "未连接" in error_msg or "not_available" in status:
            return NormalizedResult(NormalizedStatus.FAILED, PLATFORM_NOT_CONNECTED, True, False)

        if code is not None:
            code_str = str(code)
            if code == 0 or code_str in {"0", "0000000000"}:
                return NormalizedResult(NormalizedStatus.COMPLETED, None, False, False)
            if code_str in {"400", "BAD_PARAMS"} or "参数" in error_msg:
                return NormalizedResult(NormalizedStatus.FAILED, PLATFORM_BAD_PARAMS, False, False)
            if "0000900034" in code_str or "authcode" in code_str.lower() or "authcode" in error_msg.lower():
                return NormalizedResult(NormalizedStatus.AUTH_REQUIRED, PLATFORM_AUTH_REQUIRED, False, False)
            return NormalizedResult(NormalizedStatus.FAILED, PLATFORM_EXECUTION_FAILED, True, False)

        if status in {"error", "failed", "fail"}:
            return NormalizedResult(NormalizedStatus.FAILED, PLATFORM_EXECUTION_FAILED, True, False)

        if raw_result.get("result_uncertain") is True:
            return NormalizedResult(NormalizedStatus.RESULT_UNCERTAIN, PLATFORM_RESULT_UNCERTAIN, False, True)

    if isinstance(raw_result, str):
        text = raw_result.lower()
        if "success" in text or "ok" in text or "完成" in raw_result:
            return NormalizedResult(NormalizedStatus.COMPLETED, None, False, False)
        if "timeout" in text or "超时" in raw_result:
            return NormalizedResult(NormalizedStatus.TIMEOUT, PLATFORM_TIMEOUT, False, True)
        if "auth" in text or "授权" in raw_result:
            return NormalizedResult(NormalizedStatus.AUTH_REQUIRED, PLATFORM_AUTH_REQUIRED, False, False)
        return NormalizedResult(NormalizedStatus.FAILED, PLATFORM_EXECUTION_FAILED, True, False)

    return NormalizedResult(NormalizedStatus.RESULT_UNCERTAIN, PLATFORM_RESULT_UNCERTAIN, False, True)
