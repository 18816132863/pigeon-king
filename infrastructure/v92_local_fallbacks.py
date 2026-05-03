
from __future__ import annotations
from collections import deque
from typing import Any

class InProcessQueue:
    def __init__(self): self.q = deque()
    def put(self, item: Any): self.q.append(item); return {"status":"ok","side_effects":False}
    def get(self): return self.q.popleft() if self.q else None

class MemoryRedis:
    def __init__(self): self.store = {}
    def get(self, key): return self.store.get(key)
    def set(self, key, value): self.store[key] = value; return True

class MockConnector:
    def __init__(self, name: str = "mock"): self.name = name
    def call(self, action: str, payload: dict | None = None):
        return {"status":"ok", "mode":"mock", "connector":self.name, "action":action, "payload":payload or {}, "side_effects":False}

class LocalWorkflowExecutor:
    def run(self, workflow: dict):
        return {"status":"ok", "mode":"local", "workflow":workflow, "side_effects":False}
