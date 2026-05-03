"""
V14-V23 autonomous agent organs.

L3 Orchestration Layer - 编排层核心

agent_kernel 只负责:
- 目标接收 (Goal Reception)
- 任务编排 (Task Orchestration)
- 模块调度 (Module Dispatch)
- 状态汇总 (State Aggregation)

边界规则:
- 风险判断 → 调用 L5 unified_judge
- 记忆读写 → 调用 L2 memory_kernel
- 工具调用 → 调用 L4 execution/outbox
- 中断恢复 → 调用 L6 context_resume
- 结果验证 → 调用 L4 verifier
- 能力扩展 → 调用 L4 capability_extension + L5 governance
"""

# L3 编排层核心组件
from .goal_compiler import *
from .task_graph import *
from .memory_kernel import *
from .unified_judge import *
from .world_interface import *
from .capability_extension import *
from .handoff_orchestrator import *
