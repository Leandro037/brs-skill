from __future__ import annotations

import json
import os
from dataclasses import asdict

from brs.agentic import JSON_CODEC, with_provider_repair
from brs.builtin_profiles import make_json_profile
from brs.factory import brs_from_profile
from brs.providers import OpenAIResponsesProvider


def summarize(result):
    return {
        "decision": result.decision.value,
        "artifact": result.artifact,
        "failed_checks": [x.check_id for x in result.failed_checks],
        "repair_attempts": result.repair_attempts,
        "iterations": result.iterations,
        "checks": [
            {
                "id": c.check_id,
                "status": c.status.value,
                "evidence": c.evidence,
            }
            for c in result.checks
        ],
        "trace": [
            {
                "event": e.event,
                "iteration": e.iteration,
                "payload": e.payload,
            }
            for e in result.trace
        ],
    }


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set")

    provider = OpenAIResponsesProvider(
        model=os.getenv("BRS_OPENAI_MODEL", "gpt-6-luna")
    )

    base_profile = make_json_profile(
        required_keys=("name", "repetitions"),
        expected_types={"name": str, "repetitions": int},
    )

    # Known-defective artifact: missing 'name'. This gives us deterministic
    # pre-repair ground truth without relying on accidental model failure.
    defective = {"repetitions": 5}

    baseline_engine, baseline_context = brs_from_profile(
        base_profile,
        max_repair_iterations=0,
    )
    baseline = baseline_engine.validate(defective, context=baseline_context)

    provider_calls = []
    repaired_profile = with_provider_repair(
        base_profile,
        provider=provider,
        codec=JSON_CODEC,
        provider_calls=provider_calls,
        allowed_check_ids={"JSON_REQUIRED_FIELDS"},
        repair_instructions=(
            "Repair only the listed validation failures. "
            "Preserve every field that is already correct. "
            "For a missing name, add a short exercise name string."
        ),
    )

    repaired_engine, repaired_context = brs_from_profile(
        repaired_profile,
        max_repair_iterations=1,
    )
    repaired = repaired_engine.validate(defective, context=repaired_context)

    payload = {
        "experiment": "REAL_REPAIR_SMOKE_01",
        "model": os.getenv("BRS_OPENAI_MODEL", "gpt-6-luna"),
        "input_artifact": defective,
        "without_repair": summarize(baseline),
        "with_brs_openai_repair": summarize(repaired),
        "provider_calls": [
            {
                "model": call.model,
                "input_tokens": call.input_tokens,
                "output_tokens": call.output_tokens,
                "total_tokens": call.total_tokens,
                "text": call.text,
            }
            for call in provider_calls
        ],
    }

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
