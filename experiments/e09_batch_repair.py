from __future__ import annotations

import json
import os
import statistics
from copy import deepcopy

from brs.agentic import JSON_CODEC, with_provider_repair
from brs.builtin_profiles import make_json_profile
from brs.factory import brs_from_profile
from brs.providers import OpenAIResponsesProvider

SEED_CASES = []

def add(case_id, category, artifact, expected_valid):
    SEED_CASES.append({
        "case_id": case_id,
        "category": category,
        "artifact": artifact,
        "expected_valid": expected_valid,
    })

# 20 valid
for i in range(1, 21):
    add(f"V{i:02d}", "VALID", {"name": f"exercise_{i}", "repetitions": (i % 12) + 1}, True)

# 10 missing name
for i in range(1, 11):
    add(f"MN{i:02d}", "MISSING_NAME", {"repetitions": (i % 10) + 1}, False)

# 10 wrong repetitions type
for i in range(1, 11):
    add(f"RT{i:02d}", "REPETITIONS_WRONG_TYPE", {"name": f"exercise_rt_{i}", "repetitions": "five"}, False)

# 10 missing repetitions
for i in range(1, 11):
    add(f"MR{i:02d}", "MISSING_REPETITIONS", {"name": f"exercise_mr_{i}"}, False)

# 10 both fields missing
for i in range(1, 11):
    add(f"BF{i:02d}", "BOTH_FIELDS_MISSING", {}, False)


def summarize_validation(result):
    return {
        "decision": result.decision.value,
        "artifact": result.artifact,
        "failed_checks": [x.check_id for x in result.failed_checks],
        "repair_attempts": result.repair_attempts,
        "iterations": result.iterations,
        "checks": [
            {"id": c.check_id, "status": c.status.value, "evidence": c.evidence}
            for c in result.checks
        ],
    }


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set")

    model = os.getenv("BRS_OPENAI_MODEL", "gpt-6-luna")
    provider = OpenAIResponsesProvider(model=model)

    profile = make_json_profile(
        required_keys=("name", "repetitions"),
        expected_types={"name": str, "repetitions": int},
    )

    baseline_engine, baseline_context = brs_from_profile(
        profile,
        max_repair_iterations=0,
    )

    rows = []
    total_provider_calls = 0
    total_tokens = 0
    token_values = []

    for case in SEED_CASES:
        artifact = deepcopy(case["artifact"])
        baseline = baseline_engine.validate(artifact, context=baseline_context)

        provider_calls = []
        repaired_profile = with_provider_repair(
            profile,
            provider=provider,
            codec=JSON_CODEC,
            provider_calls=provider_calls,
            allowed_check_ids={"JSON_REQUIRED_FIELDS", "JSON_FIELD_TYPES"},
            repair_instructions=(
                "Repair only the listed validation failures. Preserve every field "
                "that is already valid. Ensure 'name' is a short non-empty string "
                "and 'repetitions' is a positive integer. Return only valid JSON."
            ),
        )
        repaired_engine, repaired_context = brs_from_profile(
            repaired_profile,
            max_repair_iterations=1,
        )
        repaired = repaired_engine.validate(artifact, context=repaired_context)

        case_tokens = sum(x.total_tokens or 0 for x in provider_calls)
        total_provider_calls += len(provider_calls)
        total_tokens += case_tokens
        if case_tokens:
            token_values.append(case_tokens)

        rows.append({
            "case_id": case["case_id"],
            "category": case["category"],
            "expected_valid": case["expected_valid"],
            "input_artifact": artifact,
            "baseline": summarize_validation(baseline),
            "with_brs_openai_repair": summarize_validation(repaired),
            "provider_calls": len(provider_calls),
            "tokens": case_tokens,
        })

    invalid_rows = [r for r in rows if not r["expected_valid"]]
    valid_rows = [r for r in rows if r["expected_valid"]]

    baseline_invalid_blocked = sum(r["baseline"]["decision"] == "BLOCK" for r in invalid_rows)
    baseline_valid_released = sum(r["baseline"]["decision"] == "RELEASE" for r in valid_rows)

    repaired_invalid_released = sum(r["with_brs_openai_repair"]["decision"] == "RELEASE" for r in invalid_rows)
    repaired_invalid_blocked = len(invalid_rows) - repaired_invalid_released
    repaired_valid_released = sum(r["with_brs_openai_repair"]["decision"] == "RELEASE" for r in valid_rows)

    category_summary = {}
    for category in sorted({r["category"] for r in rows}):
        cat = [r for r in rows if r["category"] == category]
        category_summary[category] = {
            "cases": len(cat),
            "baseline_release": sum(r["baseline"]["decision"] == "RELEASE" for r in cat),
            "baseline_block": sum(r["baseline"]["decision"] == "BLOCK" for r in cat),
            "post_repair_release": sum(r["with_brs_openai_repair"]["decision"] == "RELEASE" for r in cat),
            "post_repair_block": sum(r["with_brs_openai_repair"]["decision"] == "BLOCK" for r in cat),
            "provider_calls": sum(r["provider_calls"] for r in cat),
            "tokens": sum(r["tokens"] for r in cat),
        }

    summary = {
        "experiment": "E09_BATCH_REPAIR",
        "model": model,
        "total_cases": len(rows),
        "valid_cases": len(valid_rows),
        "invalid_cases": len(invalid_rows),
        "baseline_valid_released": baseline_valid_released,
        "baseline_invalid_blocked": baseline_invalid_blocked,
        "baseline_invalid_detect_rate": baseline_invalid_blocked / len(invalid_rows),
        "post_repair_valid_released": repaired_valid_released,
        "post_repair_invalid_released": repaired_invalid_released,
        "post_repair_invalid_blocked": repaired_invalid_blocked,
        "repair_success_rate_on_invalid": repaired_invalid_released / len(invalid_rows),
        "total_provider_calls": total_provider_calls,
        "total_tokens": total_tokens,
        "mean_tokens_per_provider_case": statistics.mean(token_values) if token_values else 0,
        "median_tokens_per_provider_case": statistics.median(token_values) if token_values else 0,
        "category_summary": category_summary,
        "scope_note": (
            "Controlled JSON defect-repair experiment. Invalid inputs are synthetic "
            "and known in advance. Measures detection and repair behavior, not external generalization."
        ),
    }

    payload = {"summary": summary, "cases": rows}

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
