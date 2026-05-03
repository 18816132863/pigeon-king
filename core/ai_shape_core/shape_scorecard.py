from __future__ import annotations

from .finalizer_schemas import ShapeCriterion, ShapeDimension, new_id


class ShapeScorecard:
    """Scores whether the system is an actual AI shape rather than module pile."""

    def evaluate_one_result(self, result, legacy_report: dict) -> list[ShapeCriterion]:
        checks = [
            (
                ShapeDimension.GOAL,
                "目标内核：一句话被编译成 GoalContract 和目标树",
                bool(result.goal_contract and result.goal_contract.goal_tree),
                {"goal_nodes": len(result.goal_contract.goal_tree)},
            ),
            (
                ShapeDimension.MEMORY,
                "记忆内核：短/长/语义/情节/程序记忆能参与并回写",
                bool(result.memory_writes),
                {"memory_writes": len(result.memory_writes)},
            ),
            (
                ShapeDimension.JUDGE,
                "法典裁判：每次任务都有 allow/approval/block 判定",
                bool(result.judge_decision.value),
                {"decision": result.judge_decision.value, "risk": result.risk_level.value},
            ),
            (
                ShapeDimension.WORLD,
                "世界接口：V85-V316 能力通过统一接口暴露",
                legacy_report.get("coverage", 0) >= 0.7,
                legacy_report,
            ),
            (
                ShapeDimension.DAG,
                "任务图：目标被转换为可恢复 DAG",
                bool(result.task_graph.nodes and result.task_graph.edges and result.checkpoint_id),
                {"nodes": len(result.task_graph.nodes), "edges": len(result.task_graph.edges), "checkpoint": result.checkpoint_id},
            ),
            (
                ShapeDimension.EXECUTION,
                "安全执行：低风险自动完成，高风险等待审批，敏感内容阻断",
                bool(result.execution_traces),
                {"traces": len(result.execution_traces), "auto": len(result.auto_executed_tasks), "approval": len(result.approval_tasks), "blocked": len(result.blocked_tasks)},
            ),
            (
                ShapeDimension.EXPANSION,
                "能力自扩展：缺能力时有沙箱评测/灰度/回滚方案",
                all(g.safe_expansion_plan for g in result.capability_gaps) if result.capability_gaps else True,
                {"gaps": [g.capability for g in result.capability_gaps]},
            ),
            (
                ShapeDimension.RECOVERY,
                "恢复机制：每次运行有 checkpoint 和恢复计划",
                bool(result.checkpoint_id and result.recovery_plan),
                {"checkpoint": result.checkpoint_id, "recovery_steps": len(result.recovery_plan)},
            ),
            (
                ShapeDimension.LEARNING,
                "学习闭环：执行后有记忆回写记录",
                bool(result.memory_writes),
                {"memory_writes": [m.key for m in result.memory_writes]},
            ),
        ]

        criteria = []
        for dim, name, passed, evidence in checks:
            criteria.append(ShapeCriterion(
                id=new_id("criterion"),
                dimension=dim,
                name=name,
                passed=bool(passed),
                score=1.0 if passed else 0.0,
                evidence=evidence,
            ))
        return criteria
