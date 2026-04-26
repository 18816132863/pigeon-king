from __future__ import annotations

import asyncio

from execution import SpeculativeDecoder
from execution.speculative_decoding import (
    DraftModel,
    TargetModel,
    SpeculativeDecodingConfig,
    SpeculativeDecodeConfig,
    SpeculativeResult,
    SpeculativeDecodeResult,
)


def test_speculative_decoder_import_and_instantiate() -> None:
    draft = DraftModel()
    target = TargetModel()
    decoder = SpeculativeDecoder(draft, target)
    assert decoder is not None


def test_decode_returns_result() -> None:
    draft = DraftModel()
    target = TargetModel()
    decoder = SpeculativeDecoder(draft, target)
    result = asyncio.run(decoder.decode("hello speculative decoding"))
    assert isinstance(result, SpeculativeResult)
    assert isinstance(result, SpeculativeDecodeResult)
    assert isinstance(result.tokens, list)
    assert isinstance(result.output, str)


def test_acceptance_rate_is_valid() -> None:
    draft = DraftModel()
    target = TargetModel()
    decoder = SpeculativeDecoder(draft, target)
    result = asyncio.run(decoder.decode("hello speculative decoding with bounded acceptance rate"))
    assert result.accepted_count >= 0
    assert result.rejected_count >= 0
    assert 0.0 <= result.acceptance_rate <= 1.0
    assert result.total_time >= 0


def test_disabled_decoder_uses_fallback() -> None:
    decoder = SpeculativeDecoder(config=SpeculativeDecodingConfig(enabled=False))
    result = asyncio.run(decoder.decode("fallback please"))
    assert result.fallback_used is True
    assert result.status == "disabled_fallback"
    assert result.output.startswith("fallback:")


def test_dry_run_requires_no_external_api_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)
    draft = DraftModel()
    target = TargetModel()
    decoder = SpeculativeDecoder(draft, target)
    result = asyncio.run(decoder.decode("no external api key required"))
    assert result is not None
    assert isinstance(result.tokens, list)


def test_execution_package_exports_decoder() -> None:
    from execution import SpeculativeDecoder as ExportedDecoder

    draft = DraftModel()
    target = TargetModel()
    decoder = ExportedDecoder(draft, target)
    assert isinstance(decoder, SpeculativeDecoder)


def test_draft_model_stats() -> None:
    draft = DraftModel(max_draft_tokens=4)
    stats = draft.get_stats()
    assert "model_name" in stats
    assert "call_count" in stats


def test_target_model_stats() -> None:
    target = TargetModel()
    stats = target.get_stats()
    assert "model_name" in stats
    assert "call_count" in stats


def test_backward_compatible_config_alias() -> None:
    assert SpeculativeDecodeConfig is SpeculativeDecodingConfig


def test_backward_compatible_result_alias() -> None:
    assert SpeculativeDecodeResult is SpeculativeResult
