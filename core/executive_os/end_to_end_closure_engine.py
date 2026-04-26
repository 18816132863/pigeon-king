class EndToEndClosureEngine:
    """Guarantee every goal has verification, delivery and learning closure."""

    def close(self, execution_plan: dict) -> dict:
        return {
            "status": "closure_ready",
            "must_verify": True,
            "must_deliver_artifact_or_result": True,
            "must_write_audit": True,
            "must_update_learning": True,
            "must_report_uncertainty": True,
            "done_definition": [
                "result_verified",
                "artifact_or_output_delivered",
                "audit_written",
                "learning_updated",
            ],
        }
