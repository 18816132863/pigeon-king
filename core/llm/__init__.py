"""V85 LLM model decision engine.

Public entry points:
- init_model_system()
- auto_route()/route_message()
- LLMGateway.call() or core.llm.call()
- registry / register_model_external()
"""

from core.llm.schemas import (
    Complexity,
    CostPreference,
    LatencyPreference,
    ModelInfo,
    ModelType,
    PrivacyLevel,
    Provider,
    RouteDecision,
    TaskCategory,
    TaskProfile,
)
from core.llm.model_registry import registry, Cost, Latency
from core.llm.model_discovery import discover_and_register, register_model_external, update_availability
from core.llm.model_router import auto_route, get_switch_history, init_model_system, route_message
from core.llm.llm_gateway import LLMGateway, GatewayResult, call

__all__ = [
    "registry",
    "ModelInfo",
    "ModelType",
    "Provider",
    "TaskProfile",
    "TaskCategory",
    "Complexity",
    "CostPreference",
    "LatencyPreference",
    "PrivacyLevel",
    "RouteDecision",
    "discover_and_register",
    "register_model_external",
    "update_availability",
    "auto_route",
    "route_message",
    "init_model_system",
    "get_switch_history",
    "LLMGateway",
    "GatewayResult",
    "call",
    "Cost",
    "Latency",
]
