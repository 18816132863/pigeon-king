from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional
import hashlib, time

@dataclass
class MissionContractV6:
    user_goal: str
    mission_id: str = ""
    risk_boundary: str = "L2"
    constraints: List[str] = field(default_factory=lambda: ["six_layer_architecture", "end_side_global_serial"])
    success_criteria: List[str] = field(default_factory=lambda: ["result_verified", "state_recorded", "memory_writeback_guarded"])
    autonomy_budget: Dict[str, int] = field(default_factory=lambda: {"max_steps": 60, "max_device_actions": 10, "max_memory_writes": 6})

    def __post_init__(self) -> None:
        if not self.user_goal.strip():
            raise ValueError("user_goal cannot be empty")
        if not self.mission_id:
            self.mission_id = "mission_" + hashlib.sha256(f"{self.user_goal}|{time.time()}".encode()).hexdigest()[:16]

class MissionContractCompilerV6:
    def compile(self, user_goal: str, risk_boundary: str = "L2") -> MissionContractV6:
        return MissionContractV6(user_goal=user_goal, risk_boundary=risk_boundary)

@dataclass
class PortfolioMissionV6:
    mission_id: str
    priority: int = 50
    status: str = "queued"
    dependencies: List[str] = field(default_factory=list)

class GoalPortfolioV6:
    def __init__(self) -> None:
        self.items: Dict[str, PortfolioMissionV6] = {}
    def add(self, mission: PortfolioMissionV6) -> None:
        if mission.mission_id in self.items:
            raise ValueError("duplicate mission")
        self.items[mission.mission_id] = mission
    def mark(self, mission_id: str, status: str) -> None:
        self.items[mission_id].status = status
    def ready(self) -> List[PortfolioMissionV6]:
        done = {m.mission_id for m in self.items.values() if m.status == "completed"}
        return sorted([m for m in self.items.values() if m.status == "queued" and all(d in done for d in m.dependencies)], key=lambda m: (-m.priority, m.mission_id))

@dataclass
class TaskNodeV6:
    node_id: str
    action_type: str
    depends_on: List[str] = field(default_factory=list)
    requires_approval: bool = False
    is_device_action: bool = False
    status: str = "pending"
    receipt: Optional[dict] = None

class DurableTaskGraphV6:
    def __init__(self, nodes: List[TaskNodeV6]) -> None:
        ids = [n.node_id for n in nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate node_id")
        self.nodes = {n.node_id: n for n in nodes}
        for n in nodes:
            for d in n.depends_on:
                if d not in self.nodes:
                    raise ValueError(f"missing dependency {d}")
    def ready(self) -> List[TaskNodeV6]:
        return sorted([n for n in self.nodes.values() if n.status == "pending" and all(self.nodes[d].status == "completed" for d in n.depends_on)], key=lambda n: (0 if n.is_device_action else 1, n.node_id))
    def complete(self, node_id: str, receipt: Optional[dict] = None) -> None:
        self.nodes[node_id].status = "completed"; self.nodes[node_id].receipt = receipt or {"ok": True}
    def block_dependents(self, node_id: str, reason: str) -> None:
        for n in self.nodes.values():
            if node_id in n.depends_on and n.status == "pending":
                n.status = "blocked"; n.receipt = {"reason": reason}
    def snapshot(self) -> dict:
        return {"nodes": [asdict(n) for n in self.nodes.values()]}

@dataclass
class DeviceActionV6:
    action_id: str
    tool_name: str
    idempotency_key: str
    timeout_profile: str = "default"
    verification_policy: str = "verify_after_timeout"

class EndSideSerialLaneV6:
    def __init__(self) -> None:
        self.locked = False
        self.completed_keys: set[str] = set()
        self.receipts: List[dict] = []
    def execute(self, action: DeviceActionV6, runner: Callable[[DeviceActionV6], Dict[str, Any]]) -> Dict[str, Any]:
        if action.idempotency_key in self.completed_keys:
            receipt = {"action_id": action.action_id, "tool_name": action.tool_name, "status": "skipped_idempotent"}
            self.receipts.append(receipt); return receipt
        if self.locked:
            raise RuntimeError("parallel device action blocked")
        self.locked = True
        try:
            result = runner(action)
            status = result.get("status", "success")
            if status == "action_timeout":
                status = "timeout_pending_verify"
            receipt = {"action_id": action.action_id, "tool_name": action.tool_name, "status": status, "result": result, "ts": time.time()}
            if status in {"success", "success_with_timeout_receipt"}:
                self.completed_keys.add(action.idempotency_key)
            self.receipts.append(receipt); return receipt
        finally:
            self.locked = False

class DeviceRealitySyncV6:
    def reconcile(self, receipt: Dict[str, Any], observed_state: Dict[str, Any]) -> Dict[str, Any]:
        if receipt.get("status") == "timeout_pending_verify":
            if observed_state.get("target_state_matches"):
                return {**receipt, "status": "success_with_timeout_receipt", "verified": True}
            return {**receipt, "verified": False}
        if receipt.get("status") == "device_offline":
            return {**receipt, "verified": False, "requires_probe": True}
        return {**receipt, "verified": receipt.get("status") in {"success", "success_with_timeout_receipt"}}

@dataclass
class MemoryRecordV6:
    memory_type: str
    content: str
    confidence: float = 0.7
    source: str = "agent_kernel"

class PersonalMemoryLifecycleV6:
    allowed = {"semantic", "episodic", "procedural", "preference"}
    def __init__(self) -> None:
        self.records: List[MemoryRecordV6] = []
    def commit(self, record: MemoryRecordV6) -> Dict[str, Any]:
        if record.memory_type not in self.allowed:
            return {"decision": "reject", "reason": "invalid_type"}
        if record.confidence < 0.6 or len(record.content.strip()) < 8:
            return {"decision": "reject", "reason": "quality_gate"}
        self.records.append(record)
        return {"decision": "committed", "count": len(self.records)}

class CapabilitySupplyChainV6:
    trusted = {"local_registry", "approved_connector", "internal_skill_store"}
    def assess(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        reasons = []
        if candidate.get("source") not in self.trusted:
            reasons.append("untrusted_source")
        if candidate.get("requires_code_execution") and not candidate.get("rollback_supported", False):
            reasons.append("code_without_rollback")
        return {"decision": "allow_sandbox" if not reasons else "quarantine", "reasons": reasons}

class AutonomySafetyCaseV6:
    required = ["mission_contract", "risk_boundary", "task_graph", "device_serial_lane", "memory_guard", "approval_interrupts", "rollback_plan"]
    def evaluate(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        missing = [k for k in self.required if not evidence.get(k)]
        if missing:
            return {"decision": "block", "missing": missing}
        if evidence.get("risk_boundary") in {"L4", "destructive"} and not evidence.get("human_approval"):
            return {"decision": "confirm", "reason": "high_risk_requires_approval"}
        return {"decision": "allow"}

class ScenarioSimulatorV6:
    def run(self, scenarios: List[Dict[str, Any]], evaluator: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Dict[str, Any]:
        results = [{"scenario": s.get("name", "unnamed"), **evaluator(s)} for s in scenarios]
        return {"scenario_count": len(results), "allowed": sum(r.get("decision") == "allow" for r in results), "blocked": sum(r.get("decision") == "block" for r in results), "results": results}

class SelfEvolvingOperatingAgentV6:
    architecture_layer = "L3 Orchestration"
    def __init__(self) -> None:
        self.compiler = MissionContractCompilerV6(); self.judge = AutonomySafetyCaseV6(); self.device_lane = EndSideSerialLaneV6(); self.memory = PersonalMemoryLifecycleV6()
    def plan(self, goal: str) -> Dict[str, Any]:
        contract = self.compiler.compile(goal)
        graph = DurableTaskGraphV6([
            TaskNodeV6("compile_goal", "planning"),
            TaskNodeV6("judge", "governance", ["compile_goal"]),
            TaskNodeV6("device_action", "device", ["judge"], is_device_action=True),
            TaskNodeV6("verify", "verification", ["device_action"]),
            TaskNodeV6("memory_writeback", "memory", ["verify"]),
        ])
        evidence = {"mission_contract": True, "risk_boundary": contract.risk_boundary, "task_graph": True, "device_serial_lane": True, "memory_guard": True, "approval_interrupts": True, "rollback_plan": True}
        return {"contract": asdict(contract), "graph": graph.snapshot(), "judge": self.judge.evaluate(evidence)}
    def execute_device_action(self, action: DeviceActionV6, runner: Callable[[DeviceActionV6], Dict[str, Any]]) -> Dict[str, Any]:
        return self.device_lane.execute(action, runner)
    def write_memory(self, content: str, memory_type: str = "episodic", confidence: float = 0.8) -> Dict[str, Any]:
        return self.memory.commit(MemoryRecordV6(memory_type, content, confidence))
