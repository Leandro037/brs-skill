from __future__ import annotations

import os

from brs.agentic import JSON_CODEC, generate_and_validate
from brs.builtin_profiles import make_json_profile
from brs.providers import OpenAIResponsesProvider


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit(
            "OPENAI_API_KEY is not set. Configure it in your environment first."
        )

    profile = make_json_profile(
        required_keys=("name", "repetitions"),
        expected_types={"name": str, "repetitions": int},
    )

    provider = OpenAIResponsesProvider(
        model=os.getenv("BRS_OPENAI_MODEL", "gpt-6-luna"),
    )

    result = generate_and_validate(
        prompt=(
            "Create a JSON object for a simple exercise. "
            "It must include a string field 'name' and an integer field "
            "'repetitions' greater than zero."
        ),
        profile=profile,
        provider=provider,
        codec=JSON_CODEC,
        max_repair_iterations=1,
        allowed_repair_check_ids={"JSON_REQUIRED_FIELDS"},
        generation_instructions=(
            "Generate a minimal artifact that follows the user's intent."
        ),
        repair_instructions=(
            "Repair only the validation failures. Preserve correct fields."
        ),
    )

    print("decision:", result.decision.value)
    print("artifact:", result.validation.artifact)
    print("repair_attempts:", result.validation.repair_attempts)
    print("iterations:", result.validation.iterations)
    print("provider_calls:", len(result.provider_calls))
    print("total_tokens:", result.total_tokens)

    for check in result.validation.checks:
        print(check.check_id, check.status.value, check.evidence)


if __name__ == "__main__":
    main()
