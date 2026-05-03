from __future__ import annotations

from .ai_shape_core import AIShapeCore
from .finalizer import AIShapeFinalizer
from .schemas import to_dict as result_to_dict
from .finalizer_schemas import to_dict as finalizer_to_dict


def run_main(message: str, root: str = ".ai_shape_main_state") -> dict:
    """Single callable main entry for external executors."""
    core = AIShapeCore(root)
    result = core.run(message)
    return result_to_dict(result)


def certify_final_shape(root: str = ".ai_shape_finalizer_state") -> dict:
    finalizer = AIShapeFinalizer(root)
    return finalizer_to_dict(finalizer.certify())
