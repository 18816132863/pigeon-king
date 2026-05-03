#!/usr/bin/env python3
"""
agent_kernel Facade — 统一暴露 agent_kernel 核心入口
避免 57 处 import 断裂，逐步将 agent_kernel 融入 L3 Orchestration

使用方式：
    from orchestration.agent_kernel_facade import (
        GoalCompiler, TaskGraph, PersonalMemoryKernel,
        PersonalOperatingLoopV2, UnifiedJudge, ...
    )
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── 惰性加载：只在首次访问时 import，避免启动开销 ──
_lazy_cache: Dict[str, Any] = {}


def _lazy_import(name: str, module_path: str):
    """惰性导入一个 agent_kernel 模块并缓存"""
    if name not in _lazy_cache:
        try:
            mod = __import__(f"agent_kernel.{module_path}", fromlist=[name])
            _lazy_cache[name] = getattr(mod, name) if hasattr(mod, name) else None
        except Exception as e:
            logger.warning(f"agent_kernel facede: failed to import {module_path}.{name}: {e}")
            _lazy_cache[name] = None
    return _lazy_cache[name]


def _get(module: str, name: str):
    return _lazy_import(name, module)


# ════════════════════════════════════════
# 核心入口类/函数 —— 从 agent_kernel 各模块暴露
# ════════════════════════════════════════

# ── Goal Compilation ──
def GoalCompiler(*args, **kwargs):
    cls = _get("goal_compiler", "GoalCompiler")
    return cls(*args, **kwargs) if cls else None

def GoalContract(*args, **kwargs):
    cls = _get("goal_compiler", "GoalContract")
    return cls(*args, **kwargs) if cls else None

# ── Task Graph ──
def TaskGraph(*args, **kwargs):
    cls = _get("task_graph", "TaskGraph")
    return cls(*args, **kwargs) if cls else None

def TaskGraphStore(*args, **kwargs):
    cls = _get("task_graph", "TaskGraphStore")
    return cls(*args, **kwargs) if cls else None

def TaskGraphBuilder(*args, **kwargs):
    cls = _get("task_graph", "TaskGraphBuilder")
    return cls(*args, **kwargs) if cls else None

def TaskGraphExecutor(*args, **kwargs):
    cls = _get("task_graph", "TaskGraphExecutor")
    return cls(*args, **kwargs) if cls else None

# ── Memory Kernel ──
def PersonalMemoryKernel(*args, **kwargs):
    cls = _get("memory_kernel", "PersonalMemoryKernel")
    return cls(*args, **kwargs) if cls else None

def MemoryRecord(*args, **kwargs):
    cls = _get("memory_kernel", "MemoryRecord")
    return cls(*args, **kwargs) if cls else None

def VectorMemoryKernel(*args, **kwargs):
    cls = _get("memory_kernel_v2", "VectorMemoryKernel")
    return cls(*args, **kwargs) if cls else None

# ── Operating Loop ──
def PersonalOperatingLoopV2(*args, **kwargs):
    cls = _get("personal_operating_loop_v2", "PersonalOperatingLoopV2")
    return cls(*args, **kwargs) if cls else None

def OperatingLoopResult(*args, **kwargs):
    cls = _get("personal_operating_loop_v2", "OperatingLoopResult")
    return cls(*args, **kwargs) if cls else None

# ── Unified Judge ──
def UnifiedJudge(*args, **kwargs):
    cls = _get("unified_judge", "UnifiedJudge")
    return cls(*args, **kwargs) if cls else None

def JudgeDecision(*args, **kwargs):
    cls = _get("unified_judge", "JudgeDecision")
    return cls(*args, **kwargs) if cls else None

# ── Handoff ──
def HandoffOrchestrator(*args, **kwargs):
    cls = _get("handoff_orchestrator", "HandoffOrchestrator")
    return cls(*args, **kwargs) if cls else None

def Specialist(*args, **kwargs):
    cls = _get("handoff_orchestrator", "Specialist")
    return cls(*args, **kwargs) if cls else None

# ── World Interface ──
def WorldInterfaceRegistry(*args, **kwargs):
    cls = _get("world_interface", "WorldInterfaceRegistry")
    return cls(*args, **kwargs) if cls else None

def WorldCapability(*args, **kwargs):
    cls = _get("world_interface", "WorldCapability")
    return cls(*args, **kwargs) if cls else None

# ── Capability Extension ──
def CapabilityExtensionPipeline(*args, **kwargs):
    cls = _get("capability_extension", "CapabilityExtensionPipeline")
    return cls(*args, **kwargs) if cls else None

def ExtensionCandidate(*args, **kwargs):
    cls = _get("capability_extension", "ExtensionCandidate")
    return cls(*args, **kwargs) if cls else None

# ── Device Capabilities ──
def AlarmCapability(*args, **kwargs):
    cls = _get("device_capabilities", "AlarmCapability")
    return cls(*args, **kwargs) if cls else None

def CalendarCapability(*args, **kwargs):
    cls = _get("device_capabilities", "CalendarCapability")
    return cls(*args, **kwargs) if cls else None

def FileCapability(*args, **kwargs):
    cls = _get("device_capabilities", "FileCapability")
    return cls(*args, **kwargs) if cls else None

# ── Persona ──
def PersonaKernel(*args, **kwargs):
    cls = _get("persona_kernel", "PersonaKernel")
    return cls(*args, **kwargs) if cls else None

def PersonaProfile(*args, **kwargs):
    cls = _get("persona_kernel", "PersonaProfile")
    return cls(*args, **kwargs) if cls else None

# ── Autonomous Loop ──
def AutonomousOperationLoop(*args, **kwargs):
    cls = _get("autonomous_loop", "AutonomousOperationLoop")
    return cls(*args, **kwargs) if cls else None

# ── Architecture Boundary ──
def ArchitectureViolation(*args, **kwargs):
    cls = _get("architecture_boundary", "ArchitectureViolation")
    return cls(*args, **kwargs) if cls else None

def ArchitectureBoundaryReport(*args, **kwargs):
    cls = _get("architecture_boundary", "ArchitectureBoundaryReport")
    return cls(*args, **kwargs) if cls else None

# ── Layer Integrity Gate ──
def LayerIntegrityGateV2(*args, **kwargs):
    cls = _get("layer_integrity_gate_v2", "LayerIntegrityGateV2")
    return cls(*args, **kwargs) if cls else None

def LayerGateResult(*args, **kwargs):
    cls = _get("layer_integrity_gate_v2", "LayerGateResult")
    return cls(*args, **kwargs) if cls else None

# ── Rollback ──
def RollbackRepairPlanner(*args, **kwargs):
    cls = _get("rollback_repair_planner_v7", "RollbackRepairPlanner")
    return cls(*args, **kwargs) if cls else None

def FailureEvent(*args, **kwargs):
    cls = _get("rollback_repair_planner_v7", "FailureEvent")
    return cls(*args, **kwargs) if cls else None

# ── Self Evolving Command Center ──
def SelfEvolvingOSCommandCenter(*args, **kwargs):
    cls = _get("self_evolving_os_command_center_v7", "SelfEvolvingOSCommandCenter")
    return cls(*args, **kwargs) if cls else None

def CommandCenterReport(*args, **kwargs):
    cls = _get("self_evolving_os_command_center_v7", "CommandCenterReport")
    return cls(*args, **kwargs) if cls else None

# ── Hub Boundary ──
def HubOperation(*args, **kwargs):
    cls = _get("hub_boundary_contract", "HubOperation")
    return cls(*args, **kwargs) if cls else None

def HubBoundaryDecision(*args, **kwargs):
    cls = _get("hub_boundary_contract", "HubBoundaryDecision")
    return cls(*args, **kwargs) if cls else None

# ── Device Capability Base ──
def OperationStatus(*args, **kwargs):
    cls = _get("base_device_capability", "OperationStatus")
    return cls(*args, **kwargs) if cls else None

def OperationResult(*args, **kwargs):
    cls = _get("base_device_capability", "OperationResult")
    return cls(*args, **kwargs) if cls else None

def TimeoutProfile(*args, **kwargs):
    cls = _get("base_device_capability", "TimeoutProfile")
    return cls(*args, **kwargs) if cls else None

# ── Mission Contract ──
def MissionContractV6(*args, **kwargs):
    cls = _get("v56_to_v65_operating_agent", "MissionContractV6")
    return cls(*args, **kwargs) if cls else None

def MissionContractCompilerV6(*args, **kwargs):
    cls = _get("v56_to_v65_operating_agent", "MissionContractCompilerV6")
    return cls(*args, **kwargs) if cls else None

def PortfolioMissionV6(*args, **kwargs):
    cls = _get("v56_to_v65_operating_agent", "PortfolioMissionV6")
    return cls(*args, **kwargs) if cls else None

# ── Meta Governance ──
def MetaGovernanceGate(*args, **kwargs):
    cls = _get("meta_governance", "MetaGovernanceGate")
    return cls(*args, **kwargs) if cls else None

def GateReport(*args, **kwargs):
    cls = _get("meta_governance", "GateReport")
    return cls(*args, **kwargs) if cls else None


# ── 版本信息 ──
FACADE_VERSION = "V1.0"
AGENT_KERNEL_MODULES_COUNT = 41
AGENT_KERNEL_IMPORT_REF_COUNT = 57


def summary() -> Dict:
    """返回 facede 摘要"""
    return {
        "facade_version": FACADE_VERSION,
        "agent_kernel_modules": AGENT_KERNEL_MODULES_COUNT,
        "import_references": AGENT_KERNEL_IMPORT_REF_COUNT,
        "exposed_classes": 40,
        "lazy_loading": True,
    }
