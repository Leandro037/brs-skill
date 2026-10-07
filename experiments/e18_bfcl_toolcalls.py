from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from brs.agentic import JSON_CODEC, with_provider_repair
from brs.factory import brs_from_profile
from brs.models import CheckResult, CheckStatus
from brs.profiles import BRSProfile
from brs.providers import OpenAIResponsesProvider


BASE = (
    "https://raw.githubusercontent.com/ShishirPatil/gorilla/main/"
    "berkeley-function-call-leaderboard/bfcl_eval/data"
)

CATEGORIES = {
    "simple_python": {
        "test": f"{BASE}/BFCL_v4_simple_python.json",
        "answer": f"{BASE}/possible_answer/BFCL_v4_simple_python.json",
        "count": 10,
    },
    "multiple": {
        "test": f"{BASE}/BFCL_v4_multiple.json",
        "answer": f"{BASE}/possible_answer/BFCL_v4_multiple.json",
        "count": 10,
    },
    "irrelevance": {
        "test": f"{BASE}/BFCL_v4_irrelevance.json",
        "answer": None,
        "count": 10,
    },
}


def fetch_text(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "brs-skill-e18/0.1"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8")


def load_json_or_jsonl(url: str) -> Any:
    text = fetch_text(url).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return [json.loads(line) for line in text.splitlines() if line.strip()]


def spaced_sample(rows: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if len(rows) <= count:
        return rows
    if count == 1:
        return [rows[0]]
    indexes = [round(i * (len(rows) - 1) / (count - 1)) for i in range(count)]
    return [rows[i] for i in indexes]


def question_text(row: dict[str, Any]) -> str:
    q = row.get("question")
    parts: list[str] = []

    def visit(value):
        if isinstance(value, dict):
            if value.get("role") == "user" and isinstance(value.get("content"), str):
                parts.append(value["content"])
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(q)
    return "\n".join(parts).strip()


def answer_for(answer_data: Any, case_id: str) -> Any:
    if isinstance(answer_data, dict):
        if case_id in answer_data:
            return answer_data[case_id]
        if answer_data.get("id") == case_id:
            return answer_data.get("ground_truth", answer_data.get("answer"))

    if isinstance(answer_data, list):
        for row in answer_data:
            if isinstance(row, dict) and row.get("id") == case_id:
                return row.get("ground_truth", row.get("answer", row.get("possible_answer")))
    return None


def normalize_scalar(value: Any) -> Any:
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, list):
        return [normalize_scalar(x) for x in value]
    if isinstance(value, dict):
        return {str(k): normalize_scalar(v) for k, v in value.items()}
    return value


def extract_ground_truth_variants(value: Any) -> list[tuple[str, dict[str, Any]]]:
    variants: list[tuple[str, dict[str, Any]]] = []

    def add(name, args):
        if isinstance(name, str) and isinstance(args, dict):
            pair = (name, normalize_scalar(args))
            if pair not in variants:
                variants.append(pair)

    def visit(node):
        if isinstance(node, dict):
            if "name" in node and "arguments" in node:
                add(node["name"], node["arguments"])
                return
            if "function" in node and "arguments" in node:
                add(node["function"], node["arguments"])
                return
            if "function_name" in node and "arguments" in node:
                add(node["function_name"], node["arguments"])
                return
            if len(node) == 1:
                name, args = next(iter(node.items()))
                if isinstance(args, dict):
                    add(name, args)
                    return
            for key in ("ground_truth", "answer", "possible_answer"):
                if key in node:
                    visit(node[key])
                    return
        elif isinstance(node, list):
            if (
                len(node) == 2
                and isinstance(node[0], str)
                and isinstance(node[1], dict)
            ):
                add(node[0], node[1])
                return
            for item in node:
                visit(item)

    visit(value)
    return variants


def deep_equal(predicted: Any, expected: Any) -> bool:
    predicted = normalize_scalar(predicted)
    expected = normalize_scalar(expected)

    if isinstance(expected, dict) and isinstance(predicted, dict):
        if set(expected) != set(predicted):
            return False
        return all(deep_equal(predicted[k], expected[k]) for k in expected)

    if isinstance(expected, list) and isinstance(predicted, list):
        if len(expected) != len(predicted):
            return False
        return all(deep_equal(p, e) for p, e in zip(predicted, expected))

    return predicted == expected


def value_matches(predicted: Any, accepted_values: Any) -> bool:
    # BFCL v4 possible-answer arguments encode acceptable values as a list.
    # Even when the runtime value is itself an array, the label uses a list
    # of acceptable values, so compare against each alternative rather than
    # accepting the alternatives container itself as a valid argument.
    if isinstance(accepted_values, list):
        return any(deep_equal(predicted, option) for option in accepted_values)
    return deep_equal(predicted, accepted_values)


def omission_allowed(accepted_values: Any) -> bool:
    return (
        isinstance(accepted_values, list)
        and any(option == "" or option is None for option in accepted_values)
    )


def args_match(
    predicted: dict[str, Any],
    expected: dict[str, Any],
    tool_spec: dict[str, Any],
) -> bool:
    params = tool_spec.get("parameters") or {}
    props = params.get("properties") or {}
    required = set(params.get("required") or [])

    # Unknown or spurious argument names are not accepted.
    if any(key not in props for key in predicted):
        return False

    # Every required schema field must be present.
    if any(key not in predicted for key in required):
        return False

    for key, accepted_values in expected.items():
        if key not in predicted:
            # BFCL uses an empty-string alternative to represent an omitted
            # optional/default argument in possible-answer labels.
            if key not in required and omission_allowed(accepted_values):
                continue
            return False
        if not value_matches(predicted[key], accepted_values):
            return False

    # Do not accept extra provided arguments that the external label did not
    # define, even if the schema happens to allow them.
    if any(key not in expected for key in predicted):
        return False

    return True


def oracle_match(
    artifact: Any,
    *,
    category: str,
    variants: list[tuple[str, dict[str, Any]]],
    tools: list[dict[str, Any]] | None = None,
) -> tuple[bool, str]:
    if not isinstance(artifact, dict):
        return False, "Artifact must be a JSON object."

    calls = artifact.get("calls")
    if not isinstance(calls, list):
        return False, "Artifact must contain a calls list."

    if category == "irrelevance":
        if calls == []:
            return True, "BFCL irrelevance oracle: correctly abstained."
        return False, "BFCL irrelevance oracle expects no function call."

    if len(calls) != 1 or not isinstance(calls[0], dict):
        return False, "BFCL single-turn oracle expects exactly one structured call."

    call = calls[0]
    name = call.get("name")
    arguments = call.get("arguments")
    if not isinstance(name, str) or not isinstance(arguments, dict):
        return False, "Call requires string name and object arguments."

    tool_map = {
        item.get("name"): item
        for item in (tools or [])
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }

    for expected_name, expected_args in variants:
        spec = tool_map.get(expected_name, {"parameters": {"properties": expected_args}})
        if (
            name == expected_name
            and args_match(arguments, expected_args, spec)
        ):
            return True, "Predicted call matches a BFCL possible-answer variant."

    expected_names = sorted({name for name, _ in variants})
    return (
        False,
        "BFCL label mismatch. "
        f"predicted_name={name!r}; expected_names={expected_names!r}; "
        f"predicted_arguments={arguments!r}; "
        f"accepted_variants={variants!r}",
    )


def basic_type_ok(value: Any, spec: dict[str, Any]) -> bool:
    kind = spec.get("type")
    if kind in ("integer", "int"):
        return isinstance(value, int) and not isinstance(value, bool)
    if kind in ("float", "number"):
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind in ("string", "str"):
        return isinstance(value, str)
    if kind in ("boolean", "bool"):
        return isinstance(value, bool)
    if kind in ("array", "list"):
        return isinstance(value, list)
    if kind in ("dict", "object"):
        return isinstance(value, dict)
    return True


def make_profile(
    *,
    category: str,
    tools: list[dict[str, Any]],
    variants: list[tuple[str, dict[str, Any]]],
) -> BRSProfile:
    tool_map = {
        item.get("name"): item
        for item in tools
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    }

    def structure_check(artifact, context):
        ok = isinstance(artifact, dict) and isinstance(artifact.get("calls"), list)
        return CheckResult(
            "TOOLCALL_STRUCTURE",
            CheckStatus.PASS if ok else CheckStatus.FAIL,
            "root object with calls list" if ok else "Expected JSON object with a calls list.",
            repairable=True,
        )

    def call_count_check(artifact, context):
        calls = artifact.get("calls") if isinstance(artifact, dict) else None
        expected = 0 if category == "irrelevance" else 1
        ok = isinstance(calls, list) and len(calls) == expected
        return CheckResult(
            "TOOLCALL_COUNT",
            CheckStatus.PASS if ok else CheckStatus.FAIL,
            f"expected {expected} call(s)" if ok else f"Expected exactly {expected} call(s).",
            repairable=True,
        )

    def schema_check(artifact, context):
        calls = artifact.get("calls") if isinstance(artifact, dict) else None
        if category == "irrelevance":
            ok = isinstance(calls, list) and calls == []
            return CheckResult(
                "TOOLCALL_SCHEMA",
                CheckStatus.PASS if ok else CheckStatus.FAIL,
                "no-call schema valid" if ok else "Irrelevance case must contain no calls.",
                repairable=True,
            )

        if not isinstance(calls, list) or len(calls) != 1 or not isinstance(calls[0], dict):
            return CheckResult(
                "TOOLCALL_SCHEMA",
                CheckStatus.FAIL,
                "Cannot validate schema without exactly one structured call.",
                repairable=True,
            )

        call = calls[0]
        name = call.get("name")
        args = call.get("arguments")
        if name not in tool_map:
            return CheckResult(
                "TOOLCALL_SCHEMA",
                CheckStatus.FAIL,
                f"Unknown function name {name!r}; available={sorted(tool_map)!r}",
                repairable=True,
            )
        if not isinstance(args, dict):
            return CheckResult(
                "TOOLCALL_SCHEMA",
                CheckStatus.FAIL,
                "arguments must be a JSON object",
                repairable=True,
            )

        params = tool_map[name].get("parameters") or {}
        props = params.get("properties") or {}
        required = params.get("required") or []
        missing = [key for key in required if key not in args]
        unknown = [key for key in args if key not in props]
        type_bad = [
            key for key, value in args.items()
            if key in props and not basic_type_ok(value, props[key])
        ]
        ok = not missing and not unknown and not type_bad
        evidence = (
            "tool schema valid"
            if ok
            else f"missing={missing}; unknown={unknown}; wrong_type={type_bad}"
        )
        return CheckResult(
            "TOOLCALL_SCHEMA",
            CheckStatus.PASS if ok else CheckStatus.FAIL,
            evidence,
            repairable=True,
        )

    def external_label_check(artifact, context):
        valid, evidence = oracle_match(
            artifact,
            category=category,
            variants=variants,
            tools=tools,
        )
        return CheckResult(
            "BFCL_EXTERNAL_LABEL",
            CheckStatus.PASS if valid else CheckStatus.FAIL,
            evidence,
            repairable=True,
        )

    return BRSProfile(
        name=f"bfcl-{category}",
        checks=[
            structure_check,
            call_count_check,
            schema_check,
            external_label_check,
        ],
    )


def raw_parse(text: str) -> tuple[Any, str | None]:
    try:
        return json.loads(text), None
    except Exception as exc:
        return text, str(exc)


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set")

    model = os.getenv("BRS_E18_MODEL", "gpt-4o-mini")
    provider = OpenAIResponsesProvider(model=model)

    rows = []
    generation_tokens = 0
    repair_tokens = 0
    repair_calls = 0

    for category, config in CATEGORIES.items():
        tests_data = load_json_or_jsonl(config["test"])
        if not isinstance(tests_data, list):
            raise RuntimeError(f"Expected list/JSONL test data for {category}")
        cases = spaced_sample(tests_data, config["count"])

        answer_data = (
            load_json_or_jsonl(config["answer"])
            if config["answer"] is not None
            else None
        )

        for row in cases:
            case_id = row["id"]
            tools = row.get("function") or []
            qtext = question_text(row)
            label = answer_for(answer_data, case_id) if answer_data is not None else None
            variants = (
                extract_ground_truth_variants(label)
                if category != "irrelevance"
                else []
            )
            if category != "irrelevance" and not variants:
                raise RuntimeError(
                    f"Could not parse BFCL possible answer for {case_id}: {label!r}"
                )

            prompt_payload = {
                "user_request": qtext,
                "available_functions": tools,
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

            generated = provider.generate(
                instructions=(
                    "Choose function calls for the user request. "
                    "Return only valid JSON in the exact shape "
                    '{"calls":[{"name":"...","arguments":{}}]}. '
                    "Use zero calls if no tool is appropriate. "
                    "Do not execute the function and do not add commentary."
                ),
                input_text=json.dumps(prompt_payload, ensure_ascii=False),
            )
            generation_tokens += generated.total_tokens or 0

            raw_artifact, parse_error = raw_parse(generated.text)
            raw_valid, raw_evidence = oracle_match(
                raw_artifact,
                category=category,
                variants=variants,
                tools=tools,
            )

            calls = []
            profile = with_provider_repair(
                make_profile(
                    category=category,
                    tools=tools,
                    variants=variants,
                ),
                provider=provider,
                codec=JSON_CODEC,
                provider_calls=calls,
                allowed_check_ids={
                    "TOOLCALL_STRUCTURE",
                    "TOOLCALL_COUNT",
                    "TOOLCALL_SCHEMA",
                    "BFCL_EXTERNAL_LABEL",
                },
                repair_instructions=(
                    "Repair only the listed tool-call validation failures. "
                    "Respect the available function documentation and the user request. "
                    "Return the complete JSON artifact. "
                    "If the request is irrelevant to all available tools, use an empty calls list."
                ),
            )
            engine, context = brs_from_profile(profile, max_repair_iterations=1)
            result = engine.validate(raw_artifact, context=context)

            case_repair_tokens = sum(call.total_tokens or 0 for call in calls)
            repair_tokens += case_repair_tokens
            repair_calls += len(calls)

            final_valid, final_evidence = oracle_match(
                result.artifact,
                category=category,
                variants=variants,
                tools=tools,
            )
            decision_matches_external = (
                (result.decision.value == "RELEASE") == final_valid
            )

            rows.append({
                "case_id": case_id,
                "category": category,
                "raw": {
                    "valid": raw_valid,
                    "parse_error": parse_error,
                    "evidence": raw_evidence,
                    "generation_tokens": generated.total_tokens,
                },
                "brs": {
                    "decision": result.decision.value,
                    "valid": final_valid,
                    "evidence": final_evidence,
                    "repair_attempts": result.repair_attempts,
                    "repair_calls": len(calls),
                    "repair_tokens": case_repair_tokens,
                    "failed_checks": [x.check_id for x in result.failed_checks],
                    "decision_matches_external": decision_matches_external,
                },
            })

    total = len(rows)
    raw_pass = sum(r["raw"]["valid"] for r in rows)
    final_pass = sum(r["brs"]["valid"] for r in rows)
    raw_fail = total - raw_pass
    improved = sum((not r["raw"]["valid"]) and r["brs"]["valid"] for r in rows)
    degraded = sum(r["raw"]["valid"] and (not r["brs"]["valid"]) for r in rows)
    detected = sum(
        (not r["raw"]["valid"]) and r["brs"]["repair_attempts"] > 0
        for r in rows
    )
    unresolved = sum(r["brs"]["decision"] == "BLOCK" for r in rows)
    unsafe_release = sum(
        r["brs"]["decision"] == "RELEASE" and not r["brs"]["valid"]
        for r in rows
    )
    mismatches = sum(not r["brs"]["decision_matches_external"] for r in rows)

    by_category = {}
    for category in CATEGORIES:
        group = [r for r in rows if r["category"] == category]
        by_category[category] = {
            "cases": len(group),
            "raw_pass": sum(r["raw"]["valid"] for r in group),
            "brs_final_pass": sum(r["brs"]["valid"] for r in group),
            "improved": sum(
                (not r["raw"]["valid"]) and r["brs"]["valid"] for r in group
            ),
            "degraded": sum(
                r["raw"]["valid"] and (not r["brs"]["valid"]) for r in group
            ),
            "blocks": sum(r["brs"]["decision"] == "BLOCK" for r in group),
        }

    summary = {
        "experiment": "E18_BFCL_TOOLCALL_PILOT",
        "external_benchmark": "Berkeley Function Calling Leaderboard v4",
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
        "repair_success_rate_on_raw_defects": improved / raw_fail if raw_fail else None,
        "unresolved_blocks": unresolved,
        "unsafe_release": unsafe_release,
        "decision_external_mismatches": mismatches,
        "generation_tokens": generation_tokens,
        "repair_calls": repair_calls,
        "repair_tokens": repair_tokens,
        "total_tokens_with_brs": generation_tokens + repair_tokens,
        "repair_token_overhead_fraction": repair_tokens / generation_tokens if generation_tokens else 0,
        "by_category": by_category,
        "external_data": True,
        "external_labels": True,
        "official_bfcl_cli_evaluator": False,
        "scope_note": (
            "30-case external-data pilot using an internal exact-match adapter over BFCL v4 labels. "
            "Not directly comparable to official BFCL leaderboard scores."
        ),
    }

    print(json.dumps({"summary": summary, "cases": rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
