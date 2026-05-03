from pathlib import Path


def test_v257_marketplace():
    from core.meta_autonomy_platform import CapabilityMarketplace
    r = CapabilityMarketplace().process({"goal": "推进功能", "large_batch": True, "high_risk": False, "sensitive": False})
    assert r.version == "V257"


def test_v270_credential_scanner_blocks_sensitive():
    from core.meta_autonomy_platform import CredentialHygieneScanner
    r = CredentialHygieneScanner().process({"goal": "token", "large_batch": False, "high_risk": False, "sensitive": True})
    assert r.status.value == "blocked"


def test_v271_prompt_firewall_blocks_sensitive():
    from core.meta_autonomy_platform import PromptFirewall
    r = PromptFirewall().process({"goal": "api_key", "large_batch": False, "high_risk": False, "sensitive": True})
    assert r.status.value == "blocked"


def test_v300_concurrency_warns_large_batch():
    from core.meta_autonomy_platform import ConcurrencyGovernor
    r = ConcurrencyGovernor().process({"goal": "一次多推进", "large_batch": True, "high_risk": False, "sensitive": False})
    assert r.status.value == "warn"


def test_v316_kernel(tmp_path: Path):
    from core.meta_autonomy_platform import run_meta_autonomy_platform_cycle
    r = run_meta_autonomy_platform_cycle("一次多推进60个版本", root=tmp_path)
    assert r.completed_versions == 60
    assert r.artifact_count >= 60
