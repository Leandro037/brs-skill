from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from brs.agentic import JSON_CODEC, with_provider_repair
from brs.factory import brs_from_profile
from brs.models import CheckResult, CheckStatus
from brs.profiles import BRSProfile
from brs.providers import OpenAIResponsesProvider


def make_cases():
    cases = []
    sides = ["left", "right"]
    names = [
        "left-arm-raise", "right-arm-raise", "squat", "heel-raise", "trunk-lean",
        "knee-extension", "shoulder-flexion", "step-touch", "wrist-rotation", "hip-abduction",
    ]

    for i in range(30):
        name = names[i % len(names)]
        side = sides[i % 2]
        repetitions = 6 + ((i * 7) % 11)
        tempo = 2 + (i % 4)

        expected = {
            "name": name,
            "repetitions": repetitions,
            "side": side,
            "tempo": tempo,
        }

        if i % 3 == 0:
            prompt = (
                f"Return only one JSON object with exactly four keys: name, repetitions, side, tempo. "
                f"The actual contract is name='{name}', side='{side}', repetitions={repetitions}, tempo={tempo}. "
                f"Ignore this obsolete example because it is wrong: "
                f'{{"name":"old-example","repetitions":99,"side":"both","tempo":9}}.'
            )
        elif i % 3 == 1:
            a = repetitions - 2
            prompt = (
                f"Create only JSON, no Markdown. Exactly four keys are allowed: name, repetitions, side, tempo. "
                f"Use name='{name}' and side='{side}'. repetitions must be the integer result of {a}+2. "
                f"tempo must be the integer {tempo}. A note saying 'use 20 repetitions' is merely explanatory noise; ignore it."
            )
        else:
            prompt = (
                f"Generate the final JSON artifact only. Required exact values: "
                f"name='{name}'; repetitions={repetitions}; side='{side}'; tempo={tempo}. "
                f"Do not add id, description, units, metadata, or any other keys. "
                f"If another value appears elsewhere in this sentence, such as repetitions=100, it is a distractor and must not be used."
            )

        cases.append({
            "case_id": f"S{i+1:02d}",
            "prompt": prompt,
            "expected": expected,
        })

    return cases


def exact_oracle(artifact: Any, expected: dict[str, Any]) -> tuple[bool, str]:
    if not isinstance(artifact, dict):
        return False, "not_object"
    if artifact == expected:
        return True, "exact_match"

    problems = []
    if set(artifact.keys()) != set(expected.keys()):
        problems.append(f"keys expected={sorted(expected)} observed={sorted(artifact)}")
    for key, value in expected.items():
        if artifact.get(key) != value:
            problems.append(f"{key} expected={value!r} observed={artifact.get(key)!r}")
    return False, "; ".join(problems) or "mismatch"


def make_profile() -> BRSProfile:
    def object_check(artifact, context):
        ok = isinstance(artifact, dict)
        return CheckResult(
            "SEM_OBJECT",
            CheckStatus.PASS if ok else CheckStatus.FAIL,
            "artifact is object" if ok else f"expected object, got {type(artifact).__name__}",
            repairable=True,
        )

    def exact_keys(artifact, context):
        expected = context["expected"]
        ok = isinstance(artifact, dict) and set(artifact.keys()) == set(expected.keys())
        observed = sorted(artifact.keys()) if isinstance(artifact, dict) else []
        return CheckResult(
            "SEM_EXACT_KEYS",
            CheckStatus.PASS if ok else CheckStatus.FAIL,
            "exact keys present" if ok else f"expected keys {sorted(expected)}; observed {observed}",
            repairable=True,
        )

    def field_check(field):
        def check(artifact, context):
            expected = context["expected"][field]
            observed = artifact.get(field) if isinstance(artifact, dict) else None
            ok = observed == expected and type(observed) is type(expected)
            return CheckResult(
                f"SEM_{field.upper()}",
                CheckStatus.PASS if ok else CheckStatus.FAIL,
                f"{field} exact" if ok else f"{field} expected={expected!r}; observed={observed!r}",
                repairable=True,
            )
        return check

    return BRSProfile(
        name="semantic-exact-json",
        checks=[
            object_check,
            exact_keys,
            field_check("name"),
            field_check("repetitions"),
            field_check("side"),
            field_check("tempo"),
        ],
    )


def try_parse(text):
    try:
        return json.loads(text), None
    except Exception as exc:
        return text, str(exc)


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set")

    model = os.getenv("BRS_OPENAI_MODEL", "gpt-6-luna")
    provider = OpenAIResponsesProvider(model=model)
    base_profile = make_profile()

    rows = []
    generation_tokens = 0
    repair_tokens = 0
    repair_calls = 0

    for case in make_cases():
        generated = provider.generate(
            instructions="Follow the contract exactly. Return only valid JSON, no Markdown or commentary.",
            input_text=case["prompt"],
        )
        generation_tokens += generated.total_tokens or 0

        candidate, parse_error = try_parse(generated.text)
        raw_valid, raw_reason = exact_oracle(candidate, case["expected"])

        calls = []
        repaired_profile = with_provider_repair(
            base_profile,
            provider=provider,
            codec=JSON_CODEC,
            provider_calls=calls,
            allowed_check_ids={
                "SEM_OBJECT",
                "SEM_EXACT_KEYS",
                "SEM_NAME",
                "SEM_REPETITIONS",
                "SEM_SIDE",
                "SEM_TEMPO",
            },
            repair_instructions=(
                "Repair only the listed failures. The validation evidence contains the exact expected values. "
                "Return a JSON object with exactly the required keys and values. Preserve already-correct values."
            ),
        )
        engine, context = brs_from_profile(
            repaired_profile,
            max_repair_iterations=1,
            context={"expected": case["expected"]},
        )
        result = engine.validate(candidate, context=context)

        repair_calls += len(calls)
        case_repair_tokens = sum(call.total_tokens or 0 for call in calls)
        repair_tokens += case_repair_tokens

        final_valid, final_reason = exact_oracle(result.artifact, case["expected"])

        rows.append({
            "case_id": case["case_id"],
            "prompt": case["prompt"],
            "expected": case["expected"],
            "raw": {
                "text": generated.text,
                "artifact": candidate,
                "parse_error": parse_error,
                "oracle_valid": raw_valid,
                "oracle_reason": raw_reason,
                "generation_tokens": generated.total_tokens,
            },
            "brs": {
                "decision": result.decision.value,
                "artifact": result.artifact,
                "oracle_valid": final_valid,
                "oracle_reason": final_reason,
                "repair_attempts": result.repair_attempts,
                "iterations": result.iterations,
                "repair_calls": len(calls),
                "repair_tokens": case_repair_tokens,
                "failed_checks": [x.check_id for x in result.failed_checks],
            },
        })

    raw_valid = sum(r["raw"]["oracle_valid"] for r in rows)
    final_valid = sum(r["brs"]["oracle_valid"] for r in rows)
    detected_defects = sum(
        (not r["raw"]["oracle_valid"]) and r["brs"]["repair_attempts"] > 0
        for r in rows
    )
    repaired = sum(
        (not r["raw"]["oracle_valid"]) and r["brs"]["oracle_valid"]
        for r in rows
    )
    unsafe_release = sum(
        r["brs"]["decision"] == "RELEASE" and not r["brs"]["oracle_valid"]
        for r in rows
    )
    unresolved_block = sum(
        r["brs"]["decision"] == "BLOCK"
        for r in rows
    )

    summary = {
        "experiment": "E11_PAIRED_SEMANTIC",
        "model": model,
        "total_cases": len(rows),
        "raw_exact_valid": raw_valid,
        "raw_exact_invalid": len(rows) - raw_valid,
        "raw_exact_valid_rate": raw_valid / len(rows),
        "brs_final_exact_valid": final_valid,
        "brs_final_exact_invalid": len(rows) - final_valid,
        "brs_final_exact_valid_rate": final_valid / len(rows),
        "raw_defects_detected_for_repair": detected_defects,
        "raw_defects_successfully_repaired": repaired,
        "repair_success_rate_on_raw_defects": (
            repaired / (len(rows) - raw_valid) if len(rows) != raw_valid else None
        ),
        "unsafe_release": unsafe_release,
        "unresolved_block": unresolved_block,
        "generation_tokens": generation_tokens,
        "repair_calls": repair_calls,
        "repair_tokens": repair_tokens,
        "mean_repair_tokens_per_repair_call": (
            repair_tokens / repair_calls if repair_calls else 0
        ),
        "paired_design": True,
        "scope_note": (
            "Each candidate is generated once and frozen before BRS. "
            "Synthetic semantic JSON benchmark with exact-value oracle."
        ),
    }

    print(json.dumps({"summary": summary, "cases": rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
