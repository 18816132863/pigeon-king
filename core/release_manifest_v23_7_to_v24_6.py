"""
V23.7 -> V24.6 release manifest.

This is an incremental advance package intended to be overlaid on the
existing V23.6 workspace.  It does not introduce a new architecture layer.
All new modules declare their six-layer ownership explicitly.
"""

from __future__ import annotations

RELEASE_RANGE = "V23.7_TO_V24.6"
BASELINE = "V23.6"

VERSIONS = [
    {
        "version": "V23.7",
        "name": "Action Idempotency Guard",
        "layer": "L4 Execution",
        "summary": "Protect side-effect actions from duplicate create/modify/push during retry or resume.",
    },
    {
        "version": "V23.8",
        "name": "Device Receipt Reconciler",
        "layer": "L4 Execution",
        "summary": "Treat device action timeout as pending verification, not device offline.",
    },
    {
        "version": "V23.9",
        "name": "Alarm Tool Policy",
        "layer": "L4 Execution / Platform Adapter",
        "summary": "Normalize alarm query/modify behavior and forbid broad all-range search by default.",
    },
    {
        "version": "V24.0",
        "name": "Side Effect Transaction",
        "layer": "L3 Orchestration",
        "summary": "Represent multi-channel reminder execution as a transaction with partial success semantics.",
    },
    {
        "version": "V24.1",
        "name": "End-side Workflow Contract",
        "layer": "L3 Orchestration",
        "summary": "Compile reminder workflows into fixed serial phases: alarm -> hiboard -> chat_cron -> verify.",
    },
    {
        "version": "V24.2",
        "name": "Progress Heartbeat",
        "layer": "L6 Infrastructure",
        "summary": "Write heartbeat/progress files so long tasks do not rely on chat context.",
    },
    {
        "version": "V24.3",
        "name": "Failure Taxonomy",
        "layer": "L5 Governance",
        "summary": "Classify action timeout, receipt timeout, device offline, validation errors and policy denials.",
    },
    {
        "version": "V24.4",
        "name": "Remediation Planner",
        "layer": "L3 Orchestration",
        "summary": "Map classified failures to safe remediation plans without repeating completed side effects.",
    },
    {
        "version": "V24.5",
        "name": "End-side Acceptance Matrix",
        "layer": "L3/L4/L5 Acceptance",
        "summary": "Acceptance suite for alarm timeout verification and three-channel reminder workflow.",
    },
    {
        "version": "V24.6",
        "name": "End-side Stability Gate",
        "layer": "L6 Infrastructure",
        "summary": "A final gate that checks architecture ownership, idempotency, reconciliation and remediation.",
    },
]


def version_names() -> list[str]:
    return [item["version"] for item in VERSIONS]


def assert_no_new_layer() -> bool:
    """The release must not introduce L7 or any architecture layer outside L1-L6."""
    allowed = {"L1", "L2", "L3", "L4", "L5", "L6"}
    for item in VERSIONS:
        tokens = {token.strip("/,() ") for token in item["layer"].replace("/", " ").split()}
        bad = [token for token in tokens if token.startswith("L") and token[:2] not in allowed]
        if bad:
            return False
    return True
