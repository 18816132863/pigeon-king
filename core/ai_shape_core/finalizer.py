from __future__ import annotations

from pathlib import Path

from .ai_shape_core import AIShapeCore
from .finalizer_schemas import FinalShapeReport, FinalizerStatus, ShapeCriterion, ShapeDimension, new_id
from .golden_paths import GoldenPathSuite
from .legacy_adapter import LegacyModuleAdapter
from .shape_scorecard import ShapeScorecard


class AIShapeFinalizer:
    """Finalizer that certifies the system has reached the target AI shape."""

    def __init__(self, root: str | Path = ".ai_shape_finalizer_state"):
        self.root = Path(root)
        self.core = AIShapeCore(self.root / "core_state")
        self.golden = GoldenPathSuite()
        self.legacy = LegacyModuleAdapter()
        self.scorecard = ShapeScorecard()

    def certify(self) -> FinalShapeReport:
        cases = self.golden.cases()
        golden_results = []
        first_result = None
        for case in cases:
            result = self.core.run(case.input_text)
            if first_result is None:
                first_result = result
            golden_results.append(self.golden.evaluate_result(case, result))

        legacy_report = self.legacy.inspect()
        criteria = self.scorecard.evaluate_one_result(first_result, legacy_report) if first_result else []

        golden_passed = all(r.passed for r in golden_results)
        golden_score = sum(r.score for r in golden_results) / max(1, len(golden_results))
        criteria_score = sum(c.score for c in criteria) / max(1, len(criteria))

        # Add golden path criterion.
        criteria.append(ShapeCriterion(
            id=new_id("criterion"),
            dimension=ShapeDimension.GOLDEN,
            name="黄金路径：真实场景验收通过",
            passed=golden_passed,
            score=round(golden_score, 4),
            evidence={"cases": len(golden_results), "passed": sum(1 for r in golden_results if r.passed)},
        ))

        final_score = round((criteria_score * 0.55) + (golden_score * 0.45), 4)
        failed_criteria = [c.name for c in criteria if not c.passed]
        failed_golden = [r.case_name for r in golden_results if not r.passed]

        if final_score >= 0.92 and not failed_criteria and not failed_golden:
            status = FinalizerStatus.PASS
            next_action = "最终 AI 形态已达到，可把 AIShapeCore/YuanLingSystem 作为唯一主入口。"
        elif final_score >= 0.75:
            status = FinalizerStatus.WARN
            next_action = "接近最终形态，但仍需修复失败黄金路径或缺失模块。"
        else:
            status = FinalizerStatus.FAIL
            next_action = "未达到最终形态，必须优先修复主链。"

        summary = (
            f"final_ai_shape={status.value}, score={final_score}, "
            f"criteria={sum(1 for c in criteria if c.passed)}/{len(criteria)}, "
            f"golden={sum(1 for r in golden_results if r.passed)}/{len(golden_results)}, "
            f"legacy_coverage={legacy_report.get('coverage')}"
        )

        return FinalShapeReport(
            id=new_id("final_shape_report"),
            status=status,
            final_score=final_score,
            criteria=criteria,
            golden_results=golden_results,
            main_entry="core.ai_shape_core.AIShapeCore / core.ai_shape_core.YuanLingSystem / yuanling_system.py",
            next_action=next_action,
            summary=summary,
        )
