from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
from typing import Any

from brs.agentic import TEXT_CODEC, with_provider_repair
from brs.factory import brs_from_profile
from brs.models import CheckResult, CheckStatus
from brs.profiles import BRSProfile
from brs.providers import OpenAIResponsesProvider

from evalplus.data import get_human_eval_plus
from evalplus.evaluate import check_correctness, get_groundtruth
from evalplus.eval import PASS
from evalplus.sanitize import sanitize


SELECTED_NUMBERS = list(range(0, 160, 8))[:20]


def selected_problems() -> dict[str, dict[str, Any]]:
    all_problems = get_human_eval_plus(mini=True)
    wanted = {f"HumanEval/{n}" for n in SELECTED_NUMBERS}
    selected = {task_id: problem for task_id, problem in all_problems.items() if task_id in wanted}
    if len(selected) != len(SELECTED_NUMBERS):
        missing = sorted(wanted - set(selected))
        raise RuntimeError(f"Missing selected HumanEval tasks: {missing}")
    return selected


def groundtruth_for(problems):
    digest = hashlib.sha256(
        ("E17-mini-" + ",".join(sorted(problems))).encode("utf-8")
    ).hexdigest()[:20]
    return get_groundtruth(problems, digest, [])


def failing_index(details):
    for i, ok in enumerate(details):
        if not ok:
            return i
    return None


def evaluate_candidate(code: str, problem, expected) -> tuple[bool, str, dict[str, Any]]:
    # EvalPlus may emit progress/diagnostic text to stdout. Capture it so the
    # benchmark's machine-readable JSON remains clean and reproducible.
    external_stdout = io.StringIO()
    with contextlib.redirect_stdout(external_stdout):
        result = check_correctness(
            dataset="humaneval",
            completion_id=0,
            problem=problem,
            solution=code,
            expected_output=expected,
            base_only=False,
            fast_check=False,
            identifier=problem["task_id"],
        )

    base_status, base_details = result["base"]
    plus_status, plus_details = result["plus"]
    valid = base_status == PASS and plus_status == PASS

    evidence = {
        "base_status": base_status,
        "plus_status": plus_status,
        "base_failed": sum(not x for x in base_details),
        "plus_failed": sum(not x for x in plus_details),
    }

    lines = [
        f"External EvalPlus result for {problem['task_id']}.",
        f"Task specification:\n{problem['prompt'].strip()}",
        f"base_status={base_status}; plus_status={plus_status}",
        f"base_failed={evidence['base_failed']}; plus_failed={evidence['plus_failed']}",
    ]

    bidx = failing_index(base_details)
    if bidx is not None and bidx < len(problem["base_input"]):
        lines.append(
            "One failing base test: "
            f"input={problem['base_input'][bidx]!r}; expected={expected['base'][bidx]!r}"
        )

    pidx = failing_index(plus_details)
    if pidx is not None and pidx < len(problem["plus_input"]):
        lines.append(
            "One failing plus test: "
            f"input={problem['plus_input'][pidx]!r}; expected={expected['plus'][pidx]!r}"
        )

    return valid, "\n".join(lines), evidence


def make_profile(problem, expected) -> BRSProfile:
    def external_eval_check(artifact, context):
        if not isinstance(artifact, str):
            return CheckResult(
                "EVALPLUS_HUMANEVAL_PLUS",
                CheckStatus.FAIL,
                f"Expected Python source text, got {type(artifact).__name__}",
                repairable=True,
            )
        valid, evidence, _ = evaluate_candidate(artifact, problem, expected)
        return CheckResult(
            "EVALPLUS_HUMANEVAL_PLUS",
            CheckStatus.PASS if valid else CheckStatus.FAIL,
            evidence,
            repairable=True,
        )

    return BRSProfile(
        name=f"evalplus-{problem['task_id'].replace('/', '-')}",
        checks=[external_eval_check],
    )


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set")

    model = os.getenv("BRS_E17_MODEL", "gpt-4o-mini")
    provider = OpenAIResponsesProvider(model=model)

    problems = selected_problems()
    groundtruth = groundtruth_for(problems)

    rows = []
    generation_tokens = 0
    repair_tokens = 0
    repair_calls = 0

    for task_id, problem in problems.items():
        generated = provider.generate(
            instructions=(
                "Solve the Python programming task. "
                "Return only Python source code for a complete self-contained solution. "
                "Do not use Markdown fences or commentary."
            ),
            input_text=problem["prompt"],
        )
        generation_tokens += generated.total_tokens or 0

        raw_code = sanitize(generated.text, entrypoint=problem["entry_point"])
        raw_valid, raw_evidence, raw_meta = evaluate_candidate(
            raw_code, problem, groundtruth[task_id]
        )

        calls = []
        profile = with_provider_repair(
            make_profile(problem, groundtruth[task_id]),
            provider=provider,
            codec=TEXT_CODEC,
            provider_calls=calls,
            allowed_check_ids={"EVALPLUS_HUMANEVAL_PLUS"},
            repair_instructions=(
                "Repair only the external EvalPlus test failure described in the evidence. "
                "Return only complete Python source code. "
                "Preserve already-correct behavior and the required function entry point."
            ),
        )
        engine, context = brs_from_profile(profile, max_repair_iterations=1)
        result = engine.validate(raw_code, context=context)

        case_repair_tokens = sum(call.total_tokens or 0 for call in calls)
        repair_tokens += case_repair_tokens
        repair_calls += len(calls)

        final_code = sanitize(result.artifact, entrypoint=problem["entry_point"])
        final_valid, final_evidence, final_meta = evaluate_candidate(
            final_code, problem, groundtruth[task_id]
        )

        rows.append({
            "task_id": task_id,
            "entry_point": problem["entry_point"],
            "raw": {
                "valid": raw_valid,
                "evidence": raw_evidence,
                "external": raw_meta,
                "generation_tokens": generated.total_tokens,
            },
            "brs": {
                "decision": result.decision.value,
                "valid": final_valid,
                "evidence": final_evidence,
                "external": final_meta,
                "repair_attempts": result.repair_attempts,
                "repair_calls": len(calls),
                "repair_tokens": case_repair_tokens,
                "failed_checks": [x.check_id for x in result.failed_checks],
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

    summary = {
        "experiment": "E17_EVALPLUS_HUMANEVAL_PLUS_MINI_PILOT",
        "external_benchmark": "EvalPlus HumanEval+ Mini",
        "model": model,
        "selected_task_numbers": SELECTED_NUMBERS,
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
        "generation_tokens": generation_tokens,
        "repair_calls": repair_calls,
        "repair_tokens": repair_tokens,
        "total_tokens_with_brs": generation_tokens + repair_tokens,
        "repair_token_overhead_fraction": repair_tokens / generation_tokens if generation_tokens else 0,
        "paired_design": True,
        "same_model_for_generation_and_repair": True,
        "external_oracle": True,
        "repair_feedback": "public specification + localized failing EvalPlus input/expected output",
        "scope_note": (
            "20-task external-benchmark pilot. HumanEval may be contaminated in model training; "
            "repair receives localized failing-test feedback."
        ),
    }

    print(json.dumps({"summary": summary, "cases": rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
