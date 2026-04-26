class DriftDetector:
    def detect(self, baseline: dict, current: dict) -> dict:
        changed = sorted(k for k in set(baseline) | set(current) if baseline.get(k) != current.get(k))
        return {
            "status": "drift_detected" if changed else "stable",
            "changed_keys": changed,
            "requires_review": len(changed) > 5,
        }
