class PreferenceVersioning:
    def version(self, old: dict, new: dict) -> dict:
        changed = sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))
        return {
            "status": "versioned",
            "changed_keys": changed,
            "requires_review": len(changed) > 10,
        }
