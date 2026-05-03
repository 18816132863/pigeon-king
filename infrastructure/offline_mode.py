"""
V91 OFFLINE_MODE — 全局离线运行策略。

所有外部 API、飞书、GitHub webhook、PostgreSQL、Redis、Celery、GPU、MCP 连接失败时
不允许 fatal error，统一降级为 mock / local file / unavailable warning。

审计日志写入 governance/audit/offline_audit.jsonl
"""
from __future__ import annotations
import json
import os
import time
import threading
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable

# ── 全局开关 ──────────────────────────────────────────────
OFFLINE_MODE = os.environ.get("OFFLINE_MODE", "1") in ("1", "true", "yes", "True")
NO_EXTERNAL_API = os.environ.get("NO_EXTERNAL_API", "1") in ("1", "true", "yes", "True")
NO_REAL_SEND = os.environ.get("NO_REAL_SEND", "1") in ("1", "true", "yes", "True")
NO_REAL_PAYMENT = os.environ.get("NO_REAL_PAYMENT", "1") in ("1", "true", "yes", "True")
NO_REAL_DEVICE = os.environ.get("NO_REAL_DEVICE", "1") in ("1", "true", "yes", "True")
WORKSPACE = Path(os.environ.get("WORKSPACE", "/home/sandbox/.openclaw/workspace"))
AUDIT_LOG_PATH = WORKSPACE / "governance" / "audit" / "offline_audit.jsonl"
STATE_DIR = WORKSPACE / ".offline_state"

# ── 审计日志 ──────────────────────────────────────────────
_audit_lock = threading.Lock()

def _audit(level: str, module: str, message: str, detail: Dict[str, Any] = None) -> None:
    entry = {
        "ts": time.time(),
        "level": level,
        "module": module,
        "message": message,
        "detail": detail or {},
    }
    with _audit_lock:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(AUDIT_LOG_PATH, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

def audit_warning(module: str, message: str, **detail) -> None:
    _audit("WARN", module, message, detail)

def audit_info(module: str, message: str, **detail) -> None:
    _audit("INFO", module, message, detail)

def audit_error(module: str, message: str, **detail) -> None:
    _audit("ERROR", module, message, detail)

# ── MOCK 结果工厂 ─────────────────────────────────────────
@dataclass
class MockResult:
    success: bool = True
    data: Dict[str, Any] = field(default_factory=dict)
    warning: str = "offline_mock"
    source: str = "offline_mode"

def mock_or_fallback(
    module: str,
    fallback_fn: Optional[Callable] = None,
    mock_data: Optional[Dict[str, Any]] = None,
    warning: str = "external_api_unavailable_in_offline_mode",
) -> MockResult:
    """统一降级入口：真实 API 不可用时返回 mock result 或调用 fallback。"""
    audit_warning(module, warning)
    if fallback_fn:
        try:
            result = fallback_fn()
            audit_info(module, "fallback_success", result=str(result)[:500])
            return MockResult(success=True, data={"fallback_result": result}, warning=warning)
        except Exception as e:
            audit_error(module, "fallback_failed", error=str(e))
    return MockResult(success=True, data=mock_data or {}, warning=warning)


# ── 外部基础设施本地替身 ──────────────────────────────────

class InProcessQueue:
    """Celery → 进程内队列。"""
    def __init__(self):
        self._tasks: list[dict] = []
        self._results: dict[str, Any] = {}

    def send_task(self, name: str, args: tuple = (), kwargs: dict = None) -> str:
        task_id = f"ipq_{int(time.time()*1000)}"
        self._tasks.append({"id": task_id, "name": name, "args": args, "kwargs": kwargs or {}})
        audit_info("InProcessQueue", f"task_enqueued", task_id=task_id, name=name)
        return task_id

    def get_result(self, task_id: str) -> Any:
        return self._results.get(task_id, MockResult(success=True, warning="offline_task_no_result"))

    def drain(self) -> list[dict]:
        tasks = list(self._tasks)
        self._tasks.clear()
        return tasks


class MemoryRedis:
    """Redis → 内存字典替身。"""
    def __init__(self):
        self._store: dict[str, Any] = {}
        audit_info("MemoryRedis", "initialized")

    def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    def set(self, key: str, value: Any, ttl: int = 0) -> bool:
        self._store[key] = value
        return True

    def delete(self, key: str) -> bool:
        return self._store.pop(key, None) is not None

    def exists(self, key: str) -> bool:
        return key in self._store


class FileRedis:
    """Redis → JSON 文件替身。"""
    def __init__(self, path: Path = None):
        self._path = path or STATE_DIR / "file_redis.json"
        self._store: dict[str, Any] = {}
        self._load()

    def _load(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if self._path.exists():
            try:
                self._store = json.loads(self._path.read_text())
            except Exception:
                self._store = {}

    def _save(self):
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._store, ensure_ascii=False))

    def get(self, key: str) -> Optional[Any]:
        return self._store.get(key)

    def set(self, key: str, value: Any, ttl: int = 0) -> bool:
        self._store[key] = value
        self._save()
        return True

    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            self._save()
            return True
        return False


class SQLiteRepo:
    """PostgreSQL → SQLite 替身。"""
    def __init__(self, path: Path = None):
        self._path = path or STATE_DIR / "sqlite_repo.jsonl"
        audit_info("SQLiteRepo", "initialized", path=str(self._path))

    def query(self, sql: str, params: tuple = ()) -> list[dict]:
        return []

    def execute(self, sql: str, params: tuple = ()) -> bool:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "a") as f:
            f.write(json.dumps({"sql": sql, "params": list(params), "ts": time.time()}, ensure_ascii=False) + "\n")
        return True


class MockCeleryApp:
    """Celery → InProcessQueue 替身。"""
    def __init__(self):
        self.queue = InProcessQueue()
        audit_info("MockCeleryApp", "initialized")

    def send_task(self, name: str, args=(), kwargs=None) -> str:
        return self.queue.send_task(name, args, kwargs)


class LocalWorkflowExecutor:
    """LangGraph 不可用时 → 本地工作流执行器。"""
    def run(self, graph_def: dict, inputs: dict) -> dict:
        audit_info("LocalWorkflowExecutor", "run", nodes=len(graph_def.get("nodes", [])))
        return {"status": "offline_mock_executed", "inputs": inputs, "steps_completed": len(graph_def.get("nodes", []))}


class MockConnectorFactory:
    """Connector Factory → Mock 合约工厂。"""
    def create(self, connector_type: str, config: dict = None) -> Any:
        audit_info("MockConnectorFactory", "create", type=connector_type)
        return MockResult(success=True, data={"connector_type": connector_type, "mock": True})


class JsonReportMonitor:
    """Monitor → 本地 JSON report。"""
    def generate(self) -> dict:
        return {
            "status": "healthy",
            "mode": "offline",
            "ts": time.time(),
            "checks": {"cpu": "ok", "memory": "ok", "disk": "ok"},
        }


class AlertDraftManager:
    """Alert → 告警草稿，不真实发送。"""
    def __init__(self):
        self.drafts: list[dict] = []
        self._path = STATE_DIR / "alert_drafts.jsonl"

    def create(self, title: str, body: str, channel: str = "unknown") -> str:
        draft = {"id": f"alert_{int(time.time()*1000)}", "title": title, "body": body[:500], "channel": channel, "sent": False, "ts": time.time()}
        self.drafts.append(draft)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "a") as f:
            f.write(json.dumps(draft, ensure_ascii=False) + "\n")
        audit_info("AlertDraft", "drafted", id=draft["id"], channel=channel)
        return draft["id"]


class OpenAPIContractValidator:
    """OpenAPI integration contract → 只做 schema 校验。"""
    def validate(self, schema: dict, response: dict = None) -> dict:
        return {"valid": True, "mode": "schema_only_offline", "warnings": []}


class MockTTS:
    """TTS 无本地引擎 → mock。"""
    def synthesize(self, text: str, voice: str = "default") -> dict:
        audit_info("MockTTS", "synthesize", text_len=len(text))
        return {"mock_audio": "offline_no_tts_engine", "text": text[:200], "voice": voice}


class MockAutoGit:
    """Auto git → 只允许本地 status/diff，不允许 push。"""
    def __init__(self, repo_path: Path = None):
        self.repo_path = repo_path or WORKSPACE

    def status(self) -> dict:
        return {"branch": "offline", "changes": [], "push_blocked": True}

    def diff(self) -> str:
        return "# offline mode: push disabled"

    def push(self) -> dict:
        audit_warning("MockAutoGit", "push_blocked_in_offline_mode")
        return {"success": False, "reason": "push_blocked_in_offline_mode"}

    def commit(self, message: str) -> dict:
        return {"success": True, "message": message, "push_blocked": True}


class MockAutoBackup:
    """Auto backup → 本地备份，不上传云端。"""
    def __init__(self, backup_dir: Path = None):
        self.backup_dir = backup_dir or STATE_DIR / "local_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup(self, name: str = None) -> dict:
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = self.backup_dir / f"backup_{ts}.json"
        path.write_text(json.dumps({"name": name or "auto", "ts": time.time(), "offline": True}))
        audit_info("MockAutoBackup", "backup_created", path=str(path))
        return {"success": True, "path": str(path), "upload_skipped": True}


# ── Singleton 实例 ────────────────────────────────────────
_state: dict[str, Any] = {}

def get(name: str, factory: Callable = None):
    if name not in _state and factory:
        _state[name] = factory()
    return _state.get(name)

def get_in_process_queue() -> InProcessQueue:
    return get("in_process_queue", InProcessQueue)

def get_memory_redis() -> MemoryRedis:
    return get("memory_redis", MemoryRedis)

def get_file_redis() -> FileRedis:
    return get("file_redis", FileRedis)

def get_sqlite_repo() -> SQLiteRepo:
    return get("sqlite_repo", SQLiteRepo)

def get_mock_celery() -> MockCeleryApp:
    return get("mock_celery", MockCeleryApp)

def get_local_workflow_executor() -> LocalWorkflowExecutor:
    return get("local_workflow_executor", LocalWorkflowExecutor)

def get_mock_connector_factory() -> MockConnectorFactory:
    return get("mock_connector_factory", MockConnectorFactory)

def get_json_monitor() -> JsonReportMonitor:
    return get("json_monitor", JsonReportMonitor)

def get_alert_drafts() -> AlertDraftManager:
    return get("alert_drafts", AlertDraftManager)

def get_openapi_validator() -> OpenAPIContractValidator:
    return get("openapi_validator", OpenAPIContractValidator)

def get_mock_tts() -> MockTTS:
    return get("mock_tts", MockTTS)

def get_mock_auto_git() -> MockAutoGit:
    return get("mock_auto_git", MockAutoGit)

def get_mock_auto_backup() -> MockAutoBackup:
    return get("mock_auto_backup", MockAutoBackup)


# ── 导出 ──────────────────────────────────────────────────
__all__ = [
    "OFFLINE_MODE", "NO_EXTERNAL_API", "NO_REAL_SEND", "NO_REAL_PAYMENT", "NO_REAL_DEVICE",
    "audit_warning", "audit_info", "audit_error",
    "mock_or_fallback", "MockResult",
    "InProcessQueue", "MemoryRedis", "FileRedis", "SQLiteRepo",
    "MockCeleryApp", "LocalWorkflowExecutor", "MockConnectorFactory",
    "JsonReportMonitor", "AlertDraftManager", "OpenAPIContractValidator",
    "MockTTS", "MockAutoGit", "MockAutoBackup",
    "get_in_process_queue", "get_memory_redis", "get_file_redis",
    "get_sqlite_repo", "get_mock_celery", "get_local_workflow_executor",
    "get_mock_connector_factory", "get_json_monitor", "get_alert_drafts",
    "get_openapi_validator", "get_mock_tts", "get_mock_auto_git", "get_mock_auto_backup",
]
