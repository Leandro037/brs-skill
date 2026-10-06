from __future__ import annotations

from dataclasses import dataclass, replace
import json
from typing import Any, Callable

from .factory import brs_from_profile
from .models import (
    CheckResult,
    CheckStatus,
    ValidationDecision,
    ValidationResult,
    ValidationTraceEvent,
)
from .profiles import BRSProfile
from .providers.base import ProviderResponse, TextProvider


@dataclass(frozen=True)
class ArtifactCodec:
    name: str
    parse: Callable[[str], Any]
    serialize: Callable[[Any], str]
    output_instruction: str


JSON_CODEC = ArtifactCodec(
    name="json",
    parse=json.loads,
    serialize=lambda value: json.dumps(value, ensure_ascii=False, indent=2),
    output_instruction="Return only a valid JSON value. Do not use Markdown fences or commentary.",
)

TEXT_CODEC = ArtifactCodec(
    name="text",
    parse=lambda value: value,
    serialize=lambda value: str(value),
    output_instruction="Return only the final artifact. Do not add commentary outside the artifact.",
)


@dataclass
class AgenticRunResult:
    validation: ValidationResult
    raw_generation: str
    provider_calls: list[ProviderResponse]

    @property
    def decision(self) -> ValidationDecision:
        return self.validation.decision

    @property
    def total_tokens(self) -> int | None:
        known = [call.total_tokens for call in self.provider_calls if call.total_tokens is not None]
        return sum(known) if known else None


def _make_generation_parse_failure(
    *,
    raw_generation: str,
    error: Exception,
) -> ValidationResult:
    failed = CheckResult(
        check_id="GENERATION_PARSE",
        status=CheckStatus.FAIL,
        evidence=f"generated artifact could not be parsed: {error}",
        mandatory=True,
        repairable=False,
    )
    return ValidationResult(
        decision=ValidationDecision.BLOCK,
        artifact=raw_generation,
        checks=[failed],
        failed_checks=[failed],
        repair_attempts=0,
        iterations=1,
        trace=[
            ValidationTraceEvent(
                event="generation_parse_failure",
                iteration=1,
                payload={"error": str(error)},
            )
        ],
    )


def with_provider_repair(
    profile: BRSProfile,
    *,
    provider: TextProvider,
    codec: ArtifactCodec,
    provider_calls: list[ProviderResponse],
    allowed_check_ids: set[str] | None = None,
    repair_instructions: str | None = None,
) -> BRSProfile:
    """Return a profile whose selected failures may be repaired by a provider.

    Repairability is explicit opt-in. Checks not selected remain unchanged.
    """

    wrapped_checks = []

    for check in profile.checks:
        def wrapped(artifact, context, _check=check):
            result = _check(artifact, context)
            selected = (
                result.status == CheckStatus.FAIL
                and (allowed_check_ids is None or result.check_id in allowed_check_ids)
            )
            return replace(result, repairable=True) if selected else result

        wrapped_checks.append(wrapped)

    def repair(artifact: Any, failed_checks: list[CheckResult], context: dict[str, Any]) -> Any:
        evidence = "\n".join(
            f"- {item.check_id}: {item.evidence}"
            for item in failed_checks
        )

        base_instructions = repair_instructions or (
            "You repair AI-generated artifacts. Change only what is necessary to "
            "address the listed validation failures. Preserve already-correct content."
        )

        response = provider.generate(
            instructions=f"{base_instructions}\n\n{codec.output_instruction}",
            input_text=(
                "Current artifact:\n"
                f"{codec.serialize(artifact)}\n\n"
                "Validation failures:\n"
                f"{evidence}\n\n"
                "Return the corrected artifact."
            ),
        )
        provider_calls.append(response)

        try:
            return codec.parse(response.text)
        except Exception:
            # Fail closed: returning the prior artifact ensures complete
            # revalidation sees the same unresolved defect.
            return artifact

    return BRSProfile(
        name=f"{profile.name}+provider-repair",
        checks=wrapped_checks,
        repair=repair,
        safety_gate=profile.safety_gate,
        context_defaults=dict(profile.context_defaults),
    )


def generate_and_validate(
    *,
    prompt: str,
    profile: BRSProfile,
    provider: TextProvider,
    codec: ArtifactCodec = TEXT_CODEC,
    max_repair_iterations: int = 1,
    allowed_repair_check_ids: set[str] | None = None,
    generation_instructions: str | None = None,
    repair_instructions: str | None = None,
    context: dict[str, Any] | None = None,
) -> AgenticRunResult:
    """Generate an artifact, validate it with BRS, repair, and fully revalidate."""

    calls: list[ProviderResponse] = []

    response = provider.generate(
        instructions=(
            (generation_instructions or "Generate the requested artifact.")
            + "\n\n"
            + codec.output_instruction
        ),
        input_text=prompt,
    )
    calls.append(response)

    try:
        artifact = codec.parse(response.text)
    except Exception as exc:
        return AgenticRunResult(
            validation=_make_generation_parse_failure(
                raw_generation=response.text,
                error=exc,
            ),
            raw_generation=response.text,
            provider_calls=calls,
        )

    agentic_profile = with_provider_repair(
        profile,
        provider=provider,
        codec=codec,
        provider_calls=calls,
        allowed_check_ids=allowed_repair_check_ids,
        repair_instructions=repair_instructions,
    )

    engine, merged_context = brs_from_profile(
        agentic_profile,
        max_repair_iterations=max_repair_iterations,
        context=context,
    )
    validation = engine.validate(artifact, context=merged_context)

    return AgenticRunResult(
        validation=validation,
        raw_generation=response.text,
        provider_calls=calls,
    )
