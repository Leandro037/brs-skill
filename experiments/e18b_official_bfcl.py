from __future__ import annotations

import json
import os
from typing import Any

from brs.agentic import JSON_CODEC, with_provider_repair
from brs.factory import brs_from_profile
from brs.models import CheckResult, CheckStatus
from brs.profiles import BRSProfile
from brs.providers import OpenAIResponsesProvider

from experiments.e18_bfcl_toolcalls import (
    CATEGORIES,
    answer_for,
    load_json_or_jsonl,
    question_text,
    raw_parse,
    spaced_sample,
)

from bfcl_eval.constants.enums import Language, ReturnFormat
from bfcl_eval.eval_checker.eval_runner import (
    _evaluate_single_ast_entry,
    _evaluate_single_relevance_entry,
    get_handler,
)


BFCL_SOURCE_COMMIT = "6ea57973c7a6097fd7c5915698c54c17c5b1b6c8"
BFCL_MODEL_NAME = "gpt-4o-mini-2024-07-18-FC"


def artifact_to_bfcl_wire(artifact: Any) -> Any:
    """
    Convert BRS portable JSON into the OpenAI-FC result representation
    expected by BFCL's registered OpenAI handler.

    BFCL's OpenAI FC configuration replaces dots in function names with
    underscores. We mirror that serialization rule here; correctness is
    still determined entirely by BFCL's official checker.
    """
    if not isinstance(artifact, dict):
        return artifact

    calls = artifact.get("calls")
    if not isinstance(calls, list):
        return artifact

    if not calls:
        # Official BFCL irrelevance logic treats no decodable function call
        # as abstention. For AST categories this decodes to an empty list and
        # fails the expected-call check.
        return ""

    wire = []
    for call in calls:
        if not isinstance(call, dict):
            return artifact
        name = call.get("name")
        arguments = call.get("arguments")
        if not isinstance(name, str) or not isinstance(arguments, dict):
            return artifact

        wire_name = name.replace(".", "_")
        wire.append({wire_name: json.dumps(arguments, ensure_ascii=False)})

    return wire


def official_bfcl_evaluate(
    artifact: Any,
    *,
    category: str,
    prompt_entry: dict[str, Any],
    possible_answer: Any,
    handler: Any,
) -> tuple[bool, dict[str, Any]]:
    wire = artifact_to_bfcl_wire(artifact)

    if category == "irrelevance":
        result = _evaluate_single_relevance_entry(
            handler,
            prompt_entry["id"],
            wire,
            prompt_entry,
            BFCL_MODEL_NAME,
            category,
        )
    else:
        result = _evaluate_single_ast_entry(
            handler,
            prompt_entry["id"],
            wire,
            possible_answer,
            prompt_entry,
            BFCL_MODEL_NAME,
            category,
            language=Language.PYTHON,
            return_format=ReturnFormat.PYTHON,
            has_tool_call_tag=False,
        )

    return bool(result.get("valid")), result


def compact_official_error(result: dict[str, Any]) -> dict[str, Any]:
    keep = (
        "error",
        "error_type",
        "model_result_decoded",
        "decoded_result",
    )
    return {key: result[key] for key in keep if key in result}


def make_official_profile(
    *,
    category: str,
    prompt_entry: dict[str, Any],
    possible_answer: Any,
    handler: Any,
) -> BRSProfile:
    qtext = question_text(prompt_entry)
    tools = prompt_entry.get("function") or []

    def official_check(artifact, context):
        valid, result = official_bfcl_evaluate(
            artifact,
            category=category,
            prompt_entry=prompt_entry,
            possible_answer=possible_answer,
            handler=handler,
        )

        if valid:
            evidence = "Official BFCL checker accepted the structured action."
        else:
            evidence = json.dumps(
                {
                    "user_request": qtext,
                    "available_functions": tools,
                    "official_bfcl_failure": compact_official_error(result),
                },
                ensure_ascii=False,
            )

        return CheckResult(
            check_id="BFCL_OFFICIAL_CHECKER",
            status=CheckStatus.PASS if valid else CheckStatus.FAIL,
            evidence=evidence,
            repairable=True,
        )

    return BRSProfile(
        name=f"bfcl-official-{category}",
        checks=[official_check],
    )


def build_generation_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "user_request": question_text(row),
        "available_functions": row.get("function") or [],
        "output_contract": {
            "calls": [
                {
                    "name": "function name",
                    "arguments": {"parameter": "value"},
                }
            ]
        },
        "abstention_rule": (
            "If none of the available functions is appropriate, return an empty calls list."
        ),
    }


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set")

    model = os.getenv("BRS_E18B_MODEL", "gpt-4o-mini")
    provider = OpenAIResponsesProvider(model=model)
    handler = get_handler(BFCL_MODEL_NAME)

    rows: list[dict[str, Any]] = []
    generation_tokens = 0
    repair_tokens = 0
    repair_calls = 0

    for category, config in CATEGORIES.items():
        tests_data = load_json_or_jsonl(config["test"])
        if not isinstance(tests_data, list):
            raise RuntimeError(f"Expected BFCL list/JSONL test data for {category}")
        cases = spaced_sample(tests_data, config["count"])

        answer_data = (
            load_json_or_jsonl(config["answer"])
            if config["answer"] is not None
            else None
        )

        for row in cases:
            case_id = row["id"]
            possible_answer = (
                answer_for(answer_data, case_id)
                if answer_data is not None
                else None
            )
            if category != "irrelevance" and possible_answer is None:
                raise RuntimeError(f"Missing BFCL ground truth for {case_id}")

            generated = provider.generate(
                instructions=(
                    "Choose the appropriate function call for the user request. "
                    "Return only valid JSON in the exact shape "
                    '{"calls":[{"name":"...","arguments":{}}]}. '
                    "Use an empty calls list when no available function should be called. "
                    "Do not execute any function and do not add commentary."
                ),
                input_text=json.dumps(
                    build_generation_payload(row),
                    ensure_ascii=False,
                ),
            )
            generation_tokens += generated.total_tokens or 0

            raw_artifact, parse_error = raw_parse(generated.text)
            raw_valid, raw_official = official_bfcl_evaluate(
                raw_artifact,
                category=category,
                prompt_entry=row,
                possible_answer=possible_answer,
                handler=handler,
            )

            calls = []
            profile = with_provider_repair(
                make_official_profile(
                    category=category,
                    prompt_entry=row,
                    possible_answer=possible_answer,
                    handler=handler,
                ),
                provider=provider,
                codec=JSON_CODEC,
                provider_calls=calls,
                allowed_check_ids={"BFCL_OFFICIAL_CHECKER"},
                repair_instructions=(
                    "Repair only the official BFCL validation failure. "
                    "Use the user request, available function schemas, and BFCL error evidence. "
                    "Return the complete JSON artifact in the required calls shape. "
                    "If no function is appropriate, return an empty calls list."
                ),
            )
            engine, context = brs_from_profile(profile, max_repair_iterations=1)
            result = engine.validate(raw_artifact, context=context)

            case_repair_tokens = sum(call.total_tokens or 0 for call in calls)
            repair_tokens += case_repair_tokens
            repair_calls += len(calls)

            final_valid, final_official = official_bfcl_evaluate(
                result.artifact,
                category=category,
                prompt_entry=row,
                possible_answer=possible_answer,
                handler=handler,
            )

            decision_matches_official = (
                (result.decision.value == "RELEASE") == final_valid
            )

            rows.append(
                {
                    "case_id": case_id,
                    "category": category,
                    "raw": {
                        "valid": raw_valid,
                        "parse_error": parse_error,
                        "official": compact_official_error(raw_official),
                        "generation_tokens": generated.total_tokens,
                    },
                    "brs": {
                        "decision": result.decision.value,
                        "valid": final_valid,
                        "official": compact_official_error(final_official),
                        "repair_attempts": result.repair_attempts,
                        "repair_calls": len(calls),
                        "repair_tokens": case_repair_tokens,
                        "failed_checks": [
                            item.check_id for item in result.failed_checks
                        ],
                        "decision_matches_official": decision_matches_official,
                    },
                }
            )

    total = len(rows)
    raw_pass = sum(row["raw"]["valid"] for row in rows)
    final_pass = sum(row["brs"]["valid"] for row in rows)
    raw_fail = total - raw_pass

    improved = sum(
        (not row["raw"]["valid"]) and row["brs"]["valid"] for row in rows
    )
    degraded = sum(
        row["raw"]["valid"] and (not row["brs"]["valid"]) for row in rows
    )
    detected = sum(
        (not row["raw"]["valid"]) and row["brs"]["repair_attempts"] > 0
        for row in rows
    )
    unresolved = sum(row["brs"]["decision"] == "BLOCK" for row in rows)
    unsafe_release = sum(
        row["brs"]["decision"] == "RELEASE" and not row["brs"]["valid"]
        for row in rows
    )
    mismatches = sum(
        not row["brs"]["decision_matches_official"] for row in rows
    )

    by_category = {}
    for category in CATEGORIES:
        group = [row for row in rows if row["category"] == category]
        by_category[category] = {
            "cases": len(group),
            "raw_pass": sum(row["raw"]["valid"] for row in group),
            "brs_final_pass": sum(row["brs"]["valid"] for row in group),
            "improved": sum(
                (not row["raw"]["valid"]) and row["brs"]["valid"]
                for row in group
            ),
            "degraded": sum(
                row["raw"]["valid"] and (not row["brs"]["valid"])
                for row in group
            ),
            "blocks": sum(
                row["brs"]["decision"] == "BLOCK" for row in group
            ),
        }

    summary = {
        "experiment": "E18B_OFFICIAL_BFCL_CHECKER",
        "benchmark": "Berkeley Function Calling Leaderboard v4",
        "bfcl_source_commit": BFCL_SOURCE_COMMIT,
        "official_checker_kernel": True,
        "full_bfcl_cli_submission": False,
        "bfcl_handler": BFCL_MODEL_NAME,
        "model": model,
        "total_cases": total,
        "raw_pass": raw_pass,
        "raw_fail": raw_fail,
        "raw_pass_rate": raw_pass / total,
        "brs_final_pass": final_pass,
        "brs_final_fail": total - final_pass,
        "brs_final_pass_rate": final_pass / total,
        "absolute_gain_cases": final_pass - raw_pass,
        "absolute_gain_rate_points": (final_pass - raw_pass) / total,
        "paired_improved": improved,
        "paired_degraded": degraded,
        "raw_defects_detected": detected,
        "raw_defects_repaired": improved,
        "repair_success_rate_on_raw_defects": (
            improved / raw_fail if raw_fail else None
        ),
        "unresolved_blocks": unresolved,
        "unsafe_release": unsafe_release,
        "decision_official_mismatches": mismatches,
        "generation_tokens": generation_tokens,
        "repair_calls": repair_calls,
        "repair_tokens": repair_tokens,
        "total_tokens_with_brs": generation_tokens + repair_tokens,
        "repair_token_overhead_fraction": (
            repair_tokens / generation_tokens if generation_tokens else 0
        ),
        "by_category": by_category,
        "paired_design": True,
        "validator_feedback_repair": True,
        "scope_note": (
            "30-case partial BFCL v4 pilot scored by BFCL's official checker code. "
            "Not a full leaderboard submission and not zero-feedback pass@1."
        ),
    }

    print(json.dumps({"summary": summary, "cases": rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
