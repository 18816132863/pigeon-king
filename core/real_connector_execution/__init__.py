"""
V25 Real Connector Execution.

This layer sits after V24 TopAIOperator and gives bound tools real connector
execution where safe:

- file connector: real local safe workspace artifact output
- mail connector: draft/preparation only, never sends
- calendar connector: read/draft/preparation only, never writes externally by default
- script connector: allowlisted safe commands only; otherwise dry-run / approval
- model connector: route/prepare model call through gateway when available
- action bridge connector: prepare real-world action, approval gated
- device connector: prepare device action, approval gated

External side effects remain approval_required or blocked.
"""

from .schemas import (
    ConnectorKind,
    ConnectorMode,
    ConnectorStatus,
    ConnectorExecution,
    ConnectorReport,
)
from .connector_registry import ConnectorRegistry
from .connectors import (
    FileWorkspaceConnector,
    MailDraftConnector,
    CalendarDraftConnector,
    SafeScriptConnector,
    ModelRouteConnector,
    ActionBridgeConnector,
    DevicePrepareConnector,
    GenericConnector,
)
from .connector_executor import ConnectorExecutor
from .connector_kernel import ConnectorKernel, init_connector_execution, run_connector_execution

__all__ = [
    "ConnectorKind",
    "ConnectorMode",
    "ConnectorStatus",
    "ConnectorExecution",
    "ConnectorReport",
    "ConnectorRegistry",
    "FileWorkspaceConnector",
    "MailDraftConnector",
    "CalendarDraftConnector",
    "SafeScriptConnector",
    "ModelRouteConnector",
    "ActionBridgeConnector",
    "DevicePrepareConnector",
    "GenericConnector",
    "ConnectorExecutor",
    "ConnectorKernel",
    "init_connector_execution",
    "run_connector_execution",
]
