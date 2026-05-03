from __future__ import annotations
from .schemas import (
    GoalContract,
    TaskGraph,
    TaskNode,
    TaskStatus,
    ExecutionTrace,
    JudgeDecision,
    RiskLevel,
    new_id,
)

class TaskGraphEngine:
    """Compiles a goal contract into a DAG and safely executes/dry-runs it."""

    def compile(self, contract: GoalContract, decision: JudgeDecision) -> TaskGraph:
        checkpoint_id = new_id("checkpoint")
        nodes: list[TaskNode] = []

        def add(title, kind, deps, risk, auto, approval, checkpoint=True):
            status = TaskStatus.READY
            if decision == JudgeDecision.BLOCK:
                status = TaskStatus.BLOCKED
            elif approval:
                status = TaskStatus.WAITING_APPROVAL
            node = TaskNode(
                id=new_id("task"),
                title=title,
                kind=kind,
                depends_on=deps,
                status=status,
                risk_level=risk,
                can_auto_execute=auto and decision != JudgeDecision.BLOCK,
                requires_approval=approval,
                checkpoint_required=checkpoint,
            )
            nodes.append(node)
            return node.id

        n1 = add("编译目标契约", "goal_compile", [], RiskLevel.L0_READONLY, True, False)
        n2 = add("读取记忆与偏好上下文", "memory_context", [n1], RiskLevel.L0_READONLY, True, False)
        n3 = add("策略/法典裁判", "constitution_judge", [n2], RiskLevel.L0_READONLY, True, False)
        n4 = add("生成世界接口能力清单", "world_capability_scan", [n3], RiskLevel.L0_READONLY, True, False)
        n5 = add("检测能力缺口并生成沙箱扩展方案", "capability_gap", [n4], RiskLevel.L1_LOW, True, False)
        n6 = add("构建任务执行 DAG", "task_dag", [n5], RiskLevel.L1_LOW, True, False)
        approval = contract.approval_required or decision == JudgeDecision.APPROVAL_REQUIRED
        n7 = add("执行安全自动部分", "safe_execution", [n6], RiskLevel.L2_REVERSIBLE, not approval, False)
        n8 = add("等待审批的真实副作用部分", "approval_gate", [n6], contract.risk_level, False, approval)
        n9 = add("生成 checkpoint 和恢复计划", "checkpoint_recovery", [n7, n8], RiskLevel.L1_LOW, True, False)
        n10 = add("输出完成报告并回写记忆", "completion_memory_writeback", [n9], RiskLevel.L1_LOW, True, False)

        edges = []
        for node in nodes:
            for dep in node.depends_on:
                edges.append({"from": dep, "to": node.id})
        return TaskGraph(new_id("taskgraph"), contract.id, nodes, edges, checkpoint_id)

    def execute_safe(self, graph: TaskGraph, decision: JudgeDecision) -> list[ExecutionTrace]:
        traces = []
        for node in graph.nodes:
            if node.status == TaskStatus.BLOCKED:
                traces.append(ExecutionTrace(new_id("trace"), node.id, TaskStatus.BLOCKED, decision, f"阻断：{node.title}", {"kind": node.kind}))
            elif node.requires_approval:
                traces.append(ExecutionTrace(new_id("trace"), node.id, TaskStatus.WAITING_APPROVAL, JudgeDecision.APPROVAL_REQUIRED, f"等待审批：{node.title}", {"checkpoint_id": graph.checkpoint_id}))
            elif node.can_auto_execute:
                node.status = TaskStatus.COMPLETED
                node.output = {"mode": "safe_dry_run_or_local", "completed": True}
                traces.append(ExecutionTrace(new_id("trace"), node.id, TaskStatus.COMPLETED, JudgeDecision.ALLOW, f"已安全完成：{node.title}", {"output": node.output}))
            else:
                node.status = TaskStatus.SKIPPED
                traces.append(ExecutionTrace(new_id("trace"), node.id, TaskStatus.SKIPPED, decision, f"跳过：{node.title}", {}))
        return traces
