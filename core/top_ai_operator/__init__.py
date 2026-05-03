"""
V24.0 Top AI Operator.

This is the "push to the top" package: default incoming messages go through
AIShapeCore, RealWorkEntry semantics, RealToolBinding, checkpoint/action log,
memory writeback, and final operator report.
"""

from .schemas import TopOperatorStatus, TopOperatorReport
from .top_operator import TopAIOperator, YuanLingTopOperator, init_top_operator, run_top_operator

__all__ = [
    "TopOperatorStatus",
    "TopOperatorReport",
    "TopAIOperator",
    "YuanLingTopOperator",
    "init_top_operator",
    "run_top_operator",
    "TopAIOperatorV25",
    "YuanLingTopOperatorV25",
    "init_top_operator_v25",
    "run_top_operator_v25",
]


# V25 real connector execution extension
from .top_operator_v25 import TopAIOperatorV25, YuanLingTopOperatorV25, init_top_operator_v25, run_top_operator_v25
