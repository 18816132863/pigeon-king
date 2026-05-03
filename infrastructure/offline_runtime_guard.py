"""
V104.2 Offline Runtime Guard

Purpose:
- Enforce NO_EXTERNAL_API / NO_REAL_SEND at runtime, not only in reports.
- Block common network clients and real outbound actions when offline mode is enabled.
- Fail closed with structured mock/block results instead of making real requests.

This module is intentionally lightweight and safe to import from mainline_hook,
single_runtime_entrypoint, or validation gates. It does not call external APIs.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Dict

_ACTIVE = False
_ORIGINALS: Dict[str, Any] = {}


def offline_enabled() -> bool:
    return (
        os.environ.get("OFFLINE_MODE") == "true"
        or os.environ.get("NO_EXTERNAL_API") == "true"
        or os.environ.get("DISABLE_LLM_API") == "true"
    )


def _blocked_result(action: str, reason: str, **extra: Any) -> Dict[str, Any]:
    return {
        "status": "blocked",
        "mode": "offline_runtime_guard",
        "action": action,
        "reason": reason,
        "side_effects": False,
        "requires_api": False,
        **extra,
    }


class OfflineExternalCallBlocked(RuntimeError):
    def __init__(self, action: str, reason: str = "NO_EXTERNAL_API=true"):
        super().__init__(f"{action} blocked by offline runtime guard: {reason}")
        self.action = action
        self.reason = reason


def _patch_urllib() -> bool:
    try:
        import urllib.request  # type: ignore
    except Exception:
        return False

    if "urllib.request.urlopen" not in _ORIGINALS:
        _ORIGINALS["urllib.request.urlopen"] = urllib.request.urlopen
    if "urllib.request.urlretrieve" not in _ORIGINALS:
        _ORIGINALS["urllib.request.urlretrieve"] = getattr(urllib.request, "urlretrieve", None)

    def blocked_urlopen(*args: Any, **kwargs: Any):
        raise OfflineExternalCallBlocked("urllib.request.urlopen")

    def blocked_urlretrieve(*args: Any, **kwargs: Any):
        raise OfflineExternalCallBlocked("urllib.request.urlretrieve")

    urllib.request.urlopen = blocked_urlopen  # type: ignore
    if hasattr(urllib.request, "urlretrieve"):
        urllib.request.urlretrieve = blocked_urlretrieve  # type: ignore
    return True


def _patch_requests() -> bool:
    try:
        import requests  # type: ignore
    except Exception:
        return False

    if "requests.sessions.Session.request" not in _ORIGINALS:
        _ORIGINALS["requests.sessions.Session.request"] = requests.sessions.Session.request

    def blocked_request(self: Any, method: str, url: str, **kwargs: Any):
        raise OfflineExternalCallBlocked("requests", f"NO_EXTERNAL_API=true url={url}")

    requests.sessions.Session.request = blocked_request  # type: ignore
    return True


def _patch_httpx() -> bool:
    try:
        import httpx  # type: ignore
    except Exception:
        return False

    patched = False
    if hasattr(httpx, "Client") and hasattr(httpx.Client, "request"):
        if "httpx.Client.request" not in _ORIGINALS:
            _ORIGINALS["httpx.Client.request"] = httpx.Client.request

        def blocked_client_request(self: Any, method: str, url: str, **kwargs: Any):
            raise OfflineExternalCallBlocked("httpx.Client.request", f"NO_EXTERNAL_API=true url={url}")

        httpx.Client.request = blocked_client_request  # type: ignore
        patched = True
    if hasattr(httpx, "AsyncClient") and hasattr(httpx.AsyncClient, "request"):
        if "httpx.AsyncClient.request" not in _ORIGINALS:
            _ORIGINALS["httpx.AsyncClient.request"] = httpx.AsyncClient.request

        async def blocked_async_request(self: Any, method: str, url: str, **kwargs: Any):
            raise OfflineExternalCallBlocked("httpx.AsyncClient.request", f"NO_EXTERNAL_API=true url={url}")

        httpx.AsyncClient.request = blocked_async_request  # type: ignore
        patched = True
    return patched


def _patch_subprocess() -> bool:
    if "subprocess.run" not in _ORIGINALS:
        _ORIGINALS["subprocess.run"] = subprocess.run
    if "subprocess.Popen" not in _ORIGINALS:
        _ORIGINALS["subprocess.Popen"] = subprocess.Popen

    blocked_tokens = {
        "git push", "curl ", "wget ", "scp ", "ssh ", "rsync ",
    }

    def command_text(cmd: Any) -> str:
        if isinstance(cmd, (list, tuple)):
            return " ".join(str(x) for x in cmd)
        return str(cmd)

    def guarded_run(cmd: Any, *args: Any, **kwargs: Any):
        txt = command_text(cmd)
        if os.environ.get("NO_REAL_SEND") == "true" or os.environ.get("NO_EXTERNAL_API") == "true":
            if any(tok in txt for tok in blocked_tokens):
                raise OfflineExternalCallBlocked("subprocess.run", f"outbound command blocked: {txt}")
        return _ORIGINALS["subprocess.run"](cmd, *args, **kwargs)

    class GuardedPopen(subprocess.Popen):  # type: ignore
        def __init__(self, cmd: Any, *args: Any, **kwargs: Any):
            txt = command_text(cmd)
            if os.environ.get("NO_REAL_SEND") == "true" or os.environ.get("NO_EXTERNAL_API") == "true":
                if any(tok in txt for tok in blocked_tokens):
                    raise OfflineExternalCallBlocked("subprocess.Popen", f"outbound command blocked: {txt}")
            super().__init__(cmd, *args, **kwargs)

    subprocess.run = guarded_run  # type: ignore
    subprocess.Popen = GuardedPopen  # type: ignore
    return True


def activate(reason: str = "manual") -> Dict[str, Any]:
    global _ACTIVE
    if _ACTIVE:
        return {"status": "active", "already_active": True, "reason": reason}

    if not offline_enabled():
        return {"status": "inactive", "reason": "offline flags not enabled"}

    patched = {
        "urllib": _patch_urllib(),
        "requests": _patch_requests(),
        "httpx": _patch_httpx(),
        "subprocess_outbound": _patch_subprocess(),
    }
    _ACTIVE = True
    return {
        "status": "active",
        "reason": reason,
        "patched": patched,
        "side_effects": False,
        "external_api_blocked": True,
        "real_send_blocked": os.environ.get("NO_REAL_SEND") == "true",
    }


def status() -> Dict[str, Any]:
    return {
        "active": _ACTIVE,
        "offline_enabled": offline_enabled(),
        "originals_saved": sorted(_ORIGINALS.keys()),
    }


def assert_no_external_api() -> Dict[str, Any]:
    return {
        "status": "pass" if offline_enabled() else "partial",
        "no_external_api": os.environ.get("NO_EXTERNAL_API") == "true",
        "disable_llm_api": os.environ.get("DISABLE_LLM_API") == "true",
        "no_real_send": os.environ.get("NO_REAL_SEND") == "true",
        "guard_active": _ACTIVE,
    }
