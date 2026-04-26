from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SpeculativeDecodingConfig:
    enabled: bool = True
    max_draft_tokens: int = 32
    acceptance_threshold: float = 0.8
    fallback_on_reject: bool = True
    timeout_seconds: float = 10.0
    dry_run: bool = True


# Backward-compatible alias used by earlier design docs/tests.
SpeculativeDecodeConfig = SpeculativeDecodingConfig


@dataclass
class SpeculativeResult:
    tokens: list[str] = field(default_factory=list)
    accepted_chunks: list[str] = field(default_factory=list)
    rejected_chunks: list[str] = field(default_factory=list)
    fallback_used: bool = False
    acceptance_rate: float = 0.0
    draft_model: str | None = None
    target_model: str | None = None
    status: str = "ok"
    error: str | None = None
    total_time: float = 0.0

    @property
    def output(self) -> str:
        return " ".join(self.tokens).strip()

    @property
    def accepted_count(self) -> int:
        return len(self.accepted_chunks)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected_chunks)


# Backward-compatible alias used by earlier design docs/tests.
SpeculativeDecodeResult = SpeculativeResult


class DraftModel:
    def __init__(self, model_name: str = "dry_run_draft", max_draft_tokens: int = 32) -> None:
        self.model_name = model_name
        self.max_draft_tokens = max_draft_tokens
        self.call_count = 0

    async def generate(self, prompt: str, context: dict[str, Any] | None = None) -> list[str]:
        self.call_count += 1
        normalized = " ".join(prompt.strip().split())
        if not normalized:
            return []

        words = normalized.split()
        chunks: list[str] = []
        if words:
            chunks.append(" ".join(words[: min(6, len(words))]))
        if len(words) > 6:
            chunks.append(" ".join(words[6 : min(12, len(words))]))
        if len(words) > 12:
            chunks.append("summary")

        return chunks[: max(1, min(self.max_draft_tokens, 3))]

    def get_stats(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "call_count": self.call_count,
            "max_draft_tokens": self.max_draft_tokens,
        }


class TargetModel:
    def __init__(self, model_name: str = "dry_run_target") -> None:
        self.model_name = model_name
        self.call_count = 0

    async def verify(
        self,
        prompt: str,
        draft_chunks: list[str],
        context: dict[str, Any] | None = None,
    ) -> tuple[list[str], list[str]]:
        self.call_count += 1
        accepted: list[str] = []
        rejected: list[str] = []

        for index, chunk in enumerate(draft_chunks):
            # Deterministic dry-run verification:
            # accept the first chunk and ordinary short chunks;
            # reject explicit synthetic "reject:" chunks.
            if chunk.startswith("reject:"):
                rejected.append(chunk)
            elif index == 0 or len(chunk) <= 128:
                accepted.append(chunk)
            else:
                rejected.append(chunk)

        return accepted, rejected

    async def fallback_decode(self, prompt: str, context: dict[str, Any] | None = None) -> str:
        normalized = " ".join(prompt.strip().split())
        if not normalized:
            return ""
        return f"fallback:{normalized[:120]}"

    def get_stats(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "call_count": self.call_count,
        }


class SpeculativeDecoder:
    """Dry-run friendly draft-target speculative decoding framework.

    This V9 implementation is intentionally deterministic and API-free so it can
    run in CI/sandbox without model credentials. Real model execution can later
    be plugged into DraftModel / TargetModel without changing this public API.
    """

    def __init__(
        self,
        draft_model: DraftModel | str | None = None,
        target_model: TargetModel | str | None = None,
        config: SpeculativeDecodingConfig | None = None,
    ) -> None:
        self.config = config or SpeculativeDecodingConfig()

        if isinstance(draft_model, DraftModel):
            self.draft_model = draft_model
        else:
            self.draft_model = DraftModel(model_name=draft_model or "dry_run_draft", max_draft_tokens=self.config.max_draft_tokens)

        if isinstance(target_model, TargetModel):
            self.target_model = target_model
        else:
            self.target_model = TargetModel(model_name=target_model or "dry_run_target")

    async def decode(
        self,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> SpeculativeResult:
        started = time.perf_counter()

        if not self.config.enabled:
            output = await self.target_model.fallback_decode(prompt, context)
            return SpeculativeResult(
                tokens=[output] if output else [],
                fallback_used=True,
                acceptance_rate=0.0,
                draft_model=self.draft_model.model_name,
                target_model=self.target_model.model_name,
                status="disabled_fallback",
                total_time=time.perf_counter() - started,
            )

        try:
            draft_chunks = await self.draft_model.generate(prompt, context)
            accepted, rejected = await self.target_model.verify(prompt, draft_chunks, context)

            fallback_used = bool(rejected and self.config.fallback_on_reject)
            tokens = accepted[:]

            if fallback_used:
                fallback_output = await self.target_model.fallback_decode(prompt, context)
                if fallback_output:
                    tokens.append(fallback_output)

            total = len(accepted) + len(rejected)
            acceptance_rate = len(accepted) / total if total else 0.0

            return SpeculativeResult(
                tokens=tokens,
                accepted_chunks=accepted,
                rejected_chunks=rejected,
                fallback_used=fallback_used,
                acceptance_rate=acceptance_rate,
                draft_model=self.draft_model.model_name,
                target_model=self.target_model.model_name,
                status="ok",
                total_time=time.perf_counter() - started,
            )
        except Exception as exc:
            if self.config.fallback_on_reject:
                output = await self.target_model.fallback_decode(prompt, context)
                return SpeculativeResult(
                    tokens=[output] if output else [],
                    fallback_used=True,
                    acceptance_rate=0.0,
                    draft_model=self.draft_model.model_name,
                    target_model=self.target_model.model_name,
                    status="fallback_after_error",
                    error=str(exc),
                    total_time=time.perf_counter() - started,
                )
            raise

    # Compatibility helpers for earlier dry-run design.
    async def _draft(self, prompt: str, context: dict[str, Any] | None = None) -> list[str]:
        return await self.draft_model.generate(prompt, context)

    async def _verify(
        self,
        prompt: str,
        draft_chunks: list[str],
        context: dict[str, Any] | None = None,
    ) -> tuple[list[str], list[str]]:
        return await self.target_model.verify(prompt, draft_chunks, context)

    async def _fallback_decode(self, prompt: str, context: dict[str, Any] | None = None) -> str:
        return await self.target_model.fallback_decode(prompt, context)
