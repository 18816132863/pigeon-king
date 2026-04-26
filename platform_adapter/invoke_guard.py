"""
平台调用统一防护层 - V11.0 稳态执行版

新增：
- call_coro 支持 coroutine 或 callable，先做幂等检查，避免 cached 命中时产生未 awaited coroutine 警告。
- 超时/结果不确定时副作用动作禁止自动重试。
- 统一 fallback / queued_for_delivery 返回格式。
"""

from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import time
from typing import Any, Awaitable, Callable, Optional, Union

from .error_codes import (
    PLATFORM_TIMEOUT,
    PLATFORM_EXECUTION_FAILED,
    PLATFORM_FALLBACK_USED,
)
from .result_normalizer import normalize_result, NormalizedStatus
from .user_messages import get_user_message


class InvokeResult:
    """统一调用结果"""

    def __init__(
        self,
        capability: str,
        op_name: str,
        normalized_status: str,
        error_code: Optional[str] = None,
        user_message: str = "",
        raw_result: Optional[dict] = None,
        should_retry: bool = False,
        result_uncertain: bool = False,
        side_effecting: bool = False,
        fallback_used: bool = False,
        idempotency_key: Optional[str] = None,
        elapsed_ms: int = 0,
    ):
        self.capability = capability
        self.op_name = op_name
        self.normalized_status = normalized_status
        self.error_code = error_code
        self.user_message = user_message
        self.raw_result = raw_result or {}
        self.should_retry = should_retry
        self.result_uncertain = result_uncertain
        self.side_effecting = side_effecting
        self.fallback_used = fallback_used
        self.idempotency_key = idempotency_key
        self.elapsed_ms = elapsed_ms

    def to_dict(self) -> dict:
        return {
            "capability": self.capability,
            "op_name": self.op_name,
            "normalized_status": self.normalized_status,
            "error_code": self.error_code,
            "user_message": self.user_message,
            "raw_result": self.raw_result,
            "should_retry": self.should_retry,
            "result_uncertain": self.result_uncertain,
            "side_effecting": self.side_effecting,
            "fallback_used": self.fallback_used,
            "idempotency_key": self.idempotency_key,
            "elapsed_ms": self.elapsed_ms,
        }


_idempotency_cache: dict[str, InvokeResult] = {}


def generate_idempotency_key(task_id: Optional[str], capability: str, payload: dict) -> str:
    canonical = json.dumps(payload or {}, sort_keys=True, ensure_ascii=False, default=str)
    payload_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    if task_id:
        return f"{task_id}:{capability}:{payload_hash}"
    return f"{capability}:{payload_hash}:{int(time.time() * 1000)}"


def check_idempotency(idempotency_key: str) -> Optional[InvokeResult]:
    return _idempotency_cache.get(idempotency_key)


def store_idempotency_result(idempotency_key: str, result: InvokeResult):
    _idempotency_cache[idempotency_key] = result


def _close_if_coroutine(value: Any) -> None:
    if inspect.iscoroutine(value):
        value.close()


async def _resolve_call(call_or_factory: Union[Awaitable[Any], Callable[[], Any]]) -> Any:
    if callable(call_or_factory) and not inspect.iscoroutine(call_or_factory):
        produced = call_or_factory()
    else:
        produced = call_or_factory

    if inspect.isawaitable(produced):
        return await produced
    return produced


async def guarded_platform_call(
    capability: str,
    op_name: str,
    call_coro: Union[Awaitable[Any], Callable[[], Any]],
    *,
    timeout_seconds: int = 60,
    idempotency_key: Optional[str] = None,
    side_effecting: bool = False,
    allow_fallback: bool = False,
    task_id: Optional[str] = None,
    payload: Optional[dict] = None,
) -> InvokeResult:
    """统一平台调用防护。"""
    start_time = time.time()

    if not idempotency_key:
        idempotency_key = generate_idempotency_key(task_id, capability, payload or {})

    if side_effecting:
        cached = check_idempotency(idempotency_key)
        if cached and cached.normalized_status == NormalizedStatus.COMPLETED:
            _close_if_coroutine(call_coro)
            return cached

    try:
        raw_result = await asyncio.wait_for(
            _resolve_call(call_coro),
            timeout=max(1, int(timeout_seconds)),
        )
        normalized = normalize_result(raw_result, capability, op_name)
        elapsed_ms = int((time.time() - start_time) * 1000)

        result = InvokeResult(
            capability=capability,
            op_name=op_name,
            normalized_status=normalized.status,
            error_code=normalized.error_code,
            user_message=get_user_message(normalized.status, normalized.error_code),
            raw_result=raw_result if isinstance(raw_result, dict) else {"value": raw_result},
            should_retry=bool(normalized.should_retry and not side_effecting),
            result_uncertain=bool(normalized.result_uncertain),
            side_effecting=side_effecting,
            fallback_used=False,
            idempotency_key=idempotency_key,
            elapsed_ms=elapsed_ms,
        )

        if side_effecting and normalized.status == NormalizedStatus.COMPLETED:
            store_idempotency_result(idempotency_key, result)

        return result

    except asyncio.TimeoutError:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return InvokeResult(
            capability=capability,
            op_name=op_name,
            normalized_status=NormalizedStatus.TIMEOUT,
            error_code=PLATFORM_TIMEOUT,
            user_message=get_user_message(NormalizedStatus.TIMEOUT, PLATFORM_TIMEOUT),
            raw_result={"error": f"Timeout after {timeout_seconds}s", "timeout_seconds": timeout_seconds},
            should_retry=not side_effecting,
            result_uncertain=True,
            side_effecting=side_effecting,
            fallback_used=False,
            idempotency_key=idempotency_key,
            elapsed_ms=elapsed_ms,
        )

    except Exception as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        return InvokeResult(
            capability=capability,
            op_name=op_name,
            normalized_status=NormalizedStatus.FAILED,
            error_code=PLATFORM_EXECUTION_FAILED,
            user_message=get_user_message(NormalizedStatus.FAILED, PLATFORM_EXECUTION_FAILED),
            raw_result={"error": str(e), "exception_type": type(e).__name__},
            should_retry=not side_effecting,
            result_uncertain=False,
            side_effecting=side_effecting,
            fallback_used=False,
            idempotency_key=idempotency_key,
            elapsed_ms=elapsed_ms,
        )


def create_fallback_result(
    capability: str,
    op_name: str,
    idempotency_key: Optional[str] = None,
    *,
    reason: str = "platform capability not directly available",
) -> InvokeResult:
    return InvokeResult(
        capability=capability,
        op_name=op_name,
        normalized_status=NormalizedStatus.QUEUED_FOR_DELIVERY,
        error_code=PLATFORM_FALLBACK_USED,
        user_message=get_user_message(NormalizedStatus.QUEUED_FOR_DELIVERY, PLATFORM_FALLBACK_USED),
        raw_result={"reason": reason, "queued": True},
        should_retry=False,
        result_uncertain=False,
        side_effecting=True,
        fallback_used=True,
        idempotency_key=idempotency_key,
        elapsed_ms=0,
    )
