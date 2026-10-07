from dataclasses import dataclass

from brs import ValidationDecision
from brs.agentic import ArtifactCodec, JSON_CODEC, TEXT_CODEC, generate_and_validate
from brs.builtin_profiles import make_code_profile, make_json_profile
from brs.models import CheckResult, CheckStatus
from brs.profiles import BRSProfile
from brs.providers.base import ProviderResponse


class FakeProvider:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def generate(self, *, instructions, input_text):
        self.calls.append({"instructions": instructions, "input_text": input_text})
        if not self.outputs:
            raise AssertionError("No fake output configured")
        value = self.outputs.pop(0)
        return ProviderResponse(
            text=value,
            model="fake-model",
            input_tokens=10,
            output_tokens=5,
            total_tokens=15,
        )


def test_generation_release_without_repair():
    provider = FakeProvider(['{"name":"exercise","repetitions":5}'])
    profile = make_json_profile(
        required_keys=("name", "repetitions"),
        expected_types={"name": str, "repetitions": int},
    )

    result = generate_and_validate(
        prompt="Create a valid exercise object",
        profile=profile,
        provider=provider,
        codec=JSON_CODEC,
        max_repair_iterations=1,
    )

    assert result.decision == ValidationDecision.RELEASE
    assert result.validation.repair_attempts == 0
    assert len(result.provider_calls) == 1
    assert result.total_tokens == 15


def test_generation_then_provider_repair_then_release():
    provider = FakeProvider([
        '{"repetitions":5}',
        '{"name":"exercise","repetitions":5}',
    ])
    profile = make_json_profile(
        required_keys=("name", "repetitions"),
        expected_types={"name": str, "repetitions": int},
    )

    result = generate_and_validate(
        prompt="Create an exercise object",
        profile=profile,
        provider=provider,
        codec=JSON_CODEC,
        max_repair_iterations=1,
        allowed_repair_check_ids={"JSON_REQUIRED_FIELDS"},
    )

    assert result.decision == ValidationDecision.RELEASE
    assert result.validation.repair_attempts == 1
    assert result.validation.iterations == 2
    assert result.validation.artifact["name"] == "exercise"
    assert len(result.provider_calls) == 2
    assert result.total_tokens == 30


def test_generation_parse_failure_blocks():
    provider = FakeProvider(["not json"])
    profile = make_json_profile(required_keys=("name",))

    result = generate_and_validate(
        prompt="Create JSON",
        profile=profile,
        provider=provider,
        codec=JSON_CODEC,
    )

    assert result.decision == ValidationDecision.BLOCK
    assert result.validation.failed_checks[0].check_id == "GENERATION_PARSE"
    assert len(result.provider_calls) == 1


def test_repair_parse_failure_fails_closed():
    provider = FakeProvider([
        '{"repetitions":5}',
        'still not json',
    ])
    profile = make_json_profile(
        required_keys=("name", "repetitions"),
        expected_types={"name": str, "repetitions": int},
    )

    result = generate_and_validate(
        prompt="Create an exercise object",
        profile=profile,
        provider=provider,
        codec=JSON_CODEC,
        max_repair_iterations=1,
        allowed_repair_check_ids={"JSON_REQUIRED_FIELDS"},
    )

    assert result.decision == ValidationDecision.BLOCK
    assert result.validation.repair_attempts == 1
    assert "JSON_REQUIRED_FIELDS" in [x.check_id for x in result.validation.failed_checks]


def test_code_profile_generation_blocks_bad_syntax_without_repair():
    provider = FakeProvider(["def broken(:\n    pass\n"])
    profile = make_code_profile()

    result = generate_and_validate(
        prompt="Write Python",
        profile=profile,
        provider=provider,
        codec=TEXT_CODEC,
        max_repair_iterations=0,
    )

    assert result.decision == ValidationDecision.BLOCK
    assert "CODE_PYTHON_SYNTAX" in [x.check_id for x in result.validation.failed_checks]



def test_custom_codec_normalizes_repair_before_revalidation():
    provider = FakeProvider([
        "BAD",
        "```python\nGOOD\n```",
    ])

    codec = ArtifactCodec(
        name="strip-fences",
        parse=lambda value: (
            value.replace("```python", "").replace("```", "").strip()
        ),
        serialize=str,
        output_instruction="Return only the normalized artifact.",
    )

    def normalized_check(artifact, context):
        return CheckResult(
            check_id="NORMALIZED_ARTIFACT",
            status=CheckStatus.PASS if artifact == "GOOD" else CheckStatus.FAIL,
            evidence=f"artifact={artifact!r}",
        )

    profile = BRSProfile(
        name="normalization-regression",
        checks=[normalized_check],
    )

    result = generate_and_validate(
        prompt="Return the artifact",
        profile=profile,
        provider=provider,
        codec=codec,
        max_repair_iterations=1,
        allowed_repair_check_ids={"NORMALIZED_ARTIFACT"},
    )

    assert result.decision == ValidationDecision.RELEASE
    assert result.validation.artifact == "GOOD"
    assert result.validation.repair_attempts == 1
    assert result.validation.iterations == 2
