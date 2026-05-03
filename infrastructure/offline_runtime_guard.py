"""V108.2 Offline Runtime Guard.

Runtime hard-stop for external API calls, outbound commands, and real side effects.
This is intentionally import-light and safe to activate from hooks, gates, and
runtime entrypoints.  It patches common clients only when OFFLINE/NO_EXTERNAL
flags are enabled.
"""
from __future__ import annotations

import os
import subprocess
from typing import Any, Dict

_ACTIVE = False
_ORIGINALS: Dict[str, Any] = {}

OUTBOUND_COMMAND_TOKENS = (
    "git push", "curl ", "wget ", "scp ", "ssh ", "rsync ",
    "gh release", "gh workflow", "twine upload", "npm publish",
)


def offline_enabled() -> bool:
    return (
        os.environ.get("OFFLINE_MODE") == "true"
        or os.environ.get("NO_EXTERNAL_API") == "true"
        or os.environ.get("DISABLE_LLM_API") == "true"
    )


class OfflineExternalCallBlocked(RuntimeError):
    def __init__(self, action: str, reason: str = "NO_EXTERNAL_API=true"):
        super().__init__(f"{action} blocked by offline runtime guard: {reason}")
        self.action = action
        self.reason = reason


def blocked_result(action: str, reason: str, **extra: Any) -> Dict[str, Any]:
    return {
        "status": "blocked",
        "mode": "offline_runtime_guard",
        "action": action,
        "reason": reason,
        "side_effects": False,
        "real_side_effects": 0,
        "external_api_calls": 0,
        "requires_api": False,
        **extra,
    }


def command_text(cmd: Any) -> str:
    if isinstance(cmd, (list, tuple)):
        return " ".join(str(x) for x in cmd)
    return str(cmd)


def _is_outbound_command(cmd: Any) -> bool:
    txt = command_text(cmd).lower()
    return any(tok in txt for tok in OUTBOUND_COMMAND_TOKENS)


def check_subprocess_command(cmd: Any) -> Dict[str, Any]:
    if (os.environ.get("NO_REAL_SEND") == "true" or os.environ.get("NO_EXTERNAL_API") == "true") and _is_outbound_command(cmd):
        return blocked_result("subprocess", f"outbound command blocked: {command_text(cmd)}")
    return {"status": "ok", "mode": "local_or_non_outbound", "real_side_effects": 0, "external_api_calls": 0}


def _patch_urllib() -> bool:
    try:
        import urllib.request  # type: ignore
    except Exception:
        return False
    _ORIGINALS.setdefault("urllib.request.urlopen", urllib.request.urlopen)
    _ORIGINALS.setdefault("urllib.request.urlretrieve", getattr(urllib.request, "urlretrieve", None))

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
    _ORIGINALS.setdefault("requests.sessions.Session.request", requests.sessions.Session.request)

    def blocked_request(self: Any, method: str, url: str, **kwargs: Any):
        raise OfflineExternalCallBlocked("requests", f"url={url}")

    requests.sessions.Session.request = blocked_request  # type: ignore
    return True


def _patch_httpx() -> bool:
    try:
        import httpx  # type: ignore
    except Exception:
        return False
    patched = False
    if hasattr(httpx, "Client") and hasattr(httpx.Client, "request"):
        _ORIGINALS.setdefault("httpx.Client.request", httpx.Client.request)

        def blocked_client_request(self: Any, method: str, url: str, **kwargs: Any):
            raise OfflineExternalCallBlocked("httpx.Client.request", f"url={url}")

        httpx.Client.request = blocked_client_request  # type: ignore
        patched = True
    if hasattr(httpx, "AsyncClient") and hasattr(httpx.AsyncClient, "request"):
        _ORIGINALS.setdefault("httpx.AsyncClient.request", httpx.AsyncClient.request)

        async def blocked_async_request(self: Any, method: str, url: str, **kwargs: Any):
            raise OfflineExternalCallBlocked("httpx.AsyncClient.request", f"url={url}")

        httpx.AsyncClient.request = blocked_async_request  # type: ignore
        patched = True
    return patched


def _patch_subprocess() -> bool:
    _ORIGINALS.setdefault("subprocess.run", subprocess.run)
    _ORIGINALS.setdefault("subprocess.Popen", subprocess.Popen)
    _ORIGINALS.setdefault("subprocess.call", subprocess.call)
    _ORIGINALS.setdefault("subprocess.check_call", subprocess.check_call)
    _ORIGINALS.setdefault("subprocess.check_output", subprocess.check_output)

    def guarded_run(cmd: Any, *args: Any, **kwargs: Any):
        result = check_subprocess_command(cmd)
        if result["status"] == "blocked":
            raise OfflineExternalCallBlocked("subprocess.run", result["reason"])
        return _ORIGINALS["subprocess.run"](cmd, *args, **kwargs)

    class GuardedPopen(subprocess.Popen):  # type: ignore
        def __init__(self, cmd: Any, *args: Any, **kwargs: Any):
            result = check_subprocess_command(cmd)
            if result["status"] == "blocked":
                raise OfflineExternalCallBlocked("subprocess.Popen", result["reason"])
            super().__init__(cmd, *args, **kwargs)

    def guarded_call(cmd: Any, *args: Any, **kwargs: Any):
        result = check_subprocess_command(cmd)
        if result["status"] == "blocked":
            raise OfflineExternalCallBlocked("subprocess.call", result["reason"])
        return _ORIGINALS["subprocess.call"](cmd, *args, **kwargs)

    def guarded_check_call(cmd: Any, *args: Any, **kwargs: Any):
        result = check_subprocess_command(cmd)
        if result["status"] == "blocked":
            raise OfflineExternalCallBlocked("subprocess.check_call", result["reason"])
        return _ORIGINALS["subprocess.check_call"](cmd, *args, **kwargs)

    def guarded_check_output(cmd: Any, *args: Any, **kwargs: Any):
        result = check_subprocess_command(cmd)
        if result["status"] == "blocked":
            raise OfflineExternalCallBlocked("subprocess.check_output", result["reason"])
        return _ORIGINALS["subprocess.check_output"](cmd, *args, **kwargs)

    subprocess.run = guarded_run  # type: ignore
    subprocess.Popen = GuardedPopen  # type: ignore
    subprocess.call = guarded_call  # type: ignore
    subprocess.check_call = guarded_check_call  # type: ignore
    subprocess.check_output = guarded_check_output  # type: ignore
    return True


def _patch_os_system() -> bool:
    import os as _os
    _ORIGINALS.setdefault("os.system", _os.system)

    def guarded_system(cmd: str):
        result = check_subprocess_command(cmd)
        if result["status"] == "blocked":
            raise OfflineExternalCallBlocked("os.system", result["reason"])
        return _ORIGINALS["os.system"](cmd)

    _os.system = guarded_system  # type: ignore
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
        "os_system_outbound": _patch_os_system(),
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
    return {"active": _ACTIVE, "offline_enabled": offline_enabled(), "originals_saved": sorted(_ORIGINALS.keys())}


def assert_no_external_api() -> Dict[str, Any]:
    return {
        "status": "pass" if offline_enabled() else "partial",
        "no_external_api": os.environ.get("NO_EXTERNAL_API") == "true",
        "disable_llm_api": os.environ.get("DISABLE_LLM_API") == "true",
        "no_real_send": os.environ.get("NO_REAL_SEND") == "true",
        "guard_active": _ACTIVE,
    }
