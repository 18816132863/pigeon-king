"""Bridge entrypoint for V25 Real Connector Execution."""

from core.real_connector_execution import ConnectorKernel, init_connector_execution, run_connector_execution

__all__ = ["ConnectorKernel", "init_connector_execution", "run_connector_execution"]
