from __future__ import annotations

import json
import math
import os
import random

from brs.agentic import TEXT_CODEC, with_provider_repair
from brs.factory import brs_from_profile
from brs.providers import OpenAIResponsesProvider

from experiments.e13_weaker_model_paired import TASKS, make_profile, run_hidden_tests

RUNS_PER_TASK = 20
BOOTSTRAP_SAMPLES = 20000
BOOTSTRAP_SEED = 20261007


def wilson(successes: int, n: int, z: float = 1.959963984540054) -> list[float]:
    if n == 0:
        return [0.0, 0.0]
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt((p * (1 - p) / n) + z * z / (4 * n * n)) / denom
    return [max(0.0, center - half), min(1.0, center + half)]


def exact_mcnemar_two_sided(improved: int, degraded: int) -> float:
    discordant = improved + degraded
    if discordant == 0:
        return 1.0
    k = min(improved, degraded)
    tail = sum(math.comb(discordant, i) for i in range(k + 1)) / (2 ** discordant)
    return min(1.0, 2 * tail)


def bootstrap_gain_ci(deltas: list[int]) -> list[float]:
    rng = random.Random(BOOTSTRAP_SEED)
    n = len(deltas)
    estimates = []
    for _ in range(BOOTSTRAP_SAMPLES):
        total = 0
        for _ in range(n):
            total += deltas[rng.randrange(n)]
        estimates.append(total / n)
    estimates.sort()
    lo = estimates[int(0.025 * (BOOTSTRAP_SAMPLES - 1))]
    hi = estimates[int(0.975 * (BOOTSTRAP_SAMPLES - 1))]
    return [lo, hi]


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set")

    model = os.getenv("BRS_E14_MODEL", "gpt-4o-mini")
    provider = OpenAIResponsesProvider(model=model)

    rows = []
    generation_tokens = 0
    repair_tokens = 0
    repair_calls = 0

    for task in TASKS:
        for run in range(1, RUNS_PER_TASK + 1):
            generated = provider.generate(
                instructions="Return only Python source code. No Markdown fences. No imports.",
                input_text=task["prompt"],
            )
            generation_tokens += generated.total_tokens or 0
            raw_code = generated.text
            raw_valid, raw_reason = run_hidden_tests(raw_code, task)

            calls = []
            profile = with_provider_repair(
                make_profile(task),
                provider=provider,
                codec=TEXT_CODEC,
                provider_calls=calls,
                allowed_check_ids={"CODE_STATIC_SAFE", "CODE_HIDDEN_TESTS"},
                repair_instructions=(
                    "Repair only the listed failures. Return only Python source code, no Markdown and no imports. "
                    "Use the exact failure evidence to fix the implementation. Preserve behavior that already passes."
                ),
            )
            engine, context = brs_from_profile(profile, max_repair_iterations=1)
            result = engine.validate(raw_code, context=context)

            case_repair_tokens = sum(call.total_tokens or 0 for call in calls)
            repair_tokens += case_repair_tokens
            repair_calls += len(calls)

            final_valid, final_reason = run_hidden_tests(result.artifact, task)

            rows.append({
                "case_id": f"{task['id']}_R{run:02d}",
                "task_id": task["id"],
                "run": run,
                "raw": {
                    "valid": raw_valid,
                    "reason": raw_reason,
                    "tokens": generated.total_tokens,
                },
                "brs": {
                    "decision": result.decision.value,
                    "valid": final_valid,
                    "reason": final_reason,
                    "repair_attempts": result.repair_attempts,
                    "repair_calls": len(calls),
                    "repair_tokens": case_repair_tokens,
                    "failed_checks": [x.check_id for x in result.failed_checks],
                },
            })

    n = len(rows)
    raw_pass = sum(r["raw"]["valid"] for r in rows)
    final_pass = sum(r["brs"]["valid"] for r in rows)

    improved = sum((not r["raw"]["valid"]) and r["brs"]["valid"] for r in rows)
    degraded = sum(r["raw"]["valid"] and (not r["brs"]["valid"]) for r in rows)
    unchanged_pass = sum(r["raw"]["valid"] and r["brs"]["valid"] for r in rows)
    unchanged_fail = sum((not r["raw"]["valid"]) and (not r["brs"]["valid"]) for r in rows)

    raw_fail = n - raw_pass
    detected = sum((not r["raw"]["valid"]) and r["brs"]["repair_attempts"] > 0 for r in rows)
    unsafe_release = sum(r["brs"]["decision"] == "RELEASE" and not r["brs"]["valid"] for r in rows)
    unresolved_blocks = sum(r["brs"]["decision"] == "BLOCK" for r in rows)

    deltas = [int(r["brs"]["valid"]) - int(r["raw"]["valid"]) for r in rows]

    by_task = {}
    for task in TASKS:
        group = [r for r in rows if r["task_id"] == task["id"]]
        raw_ok = sum(x["raw"]["valid"] for x in group)
        final_ok = sum(x["brs"]["valid"] for x in group)
        by_task[task["id"]] = {
            "cases": len(group),
            "raw_pass": raw_ok,
            "brs_final_pass": final_ok,
            "improved": sum((not x["raw"]["valid"]) and x["brs"]["valid"] for x in group),
            "unresolved": sum((not x["brs"]["valid"]) for x in group),
            "repair_calls": sum(x["brs"]["repair_calls"] for x in group),
        }

    summary = {
        "experiment": "E14_E13_REPLICATION",
        "model": model,
        "tasks": len(TASKS),
        "runs_per_task": RUNS_PER_TASK,
        "total_cases": n,
        "raw_pass": raw_pass,
        "raw_fail": raw_fail,
        "raw_pass_rate": raw_pass / n,
        "raw_pass_rate_ci95_wilson": wilson(raw_pass, n),
        "brs_final_pass": final_pass,
        "brs_final_fail": n - final_pass,
        "brs_final_pass_rate": final_pass / n,
        "brs_final_pass_rate_ci95_wilson": wilson(final_pass, n),
        "absolute_gain_cases": final_pass - raw_pass,
        "absolute_gain_rate": (final_pass - raw_pass) / n,
        "absolute_gain_ci95_paired_bootstrap": bootstrap_gain_ci(deltas),
        "paired_improved": improved,
        "paired_degraded": degraded,
        "paired_unchanged_pass": unchanged_pass,
        "paired_unchanged_fail": unchanged_fail,
        "mcnemar_exact_two_sided_p": exact_mcnemar_two_sided(improved, degraded),
        "raw_defects_detected": detected,
        "raw_defects_repaired": improved,
        "repair_success_rate_on_raw_defects": improved / raw_fail if raw_fail else None,
        "unsafe_release": unsafe_release,
        "unresolved_blocks": unresolved_blocks,
        "generation_tokens": generation_tokens,
        "repair_calls": repair_calls,
        "repair_tokens": repair_tokens,
        "total_tokens_with_brs": generation_tokens + repair_tokens,
        "repair_token_overhead_fraction": repair_tokens / generation_tokens if generation_tokens else 0,
        "by_task": by_task,
        "paired_design": True,
        "same_model_for_generation_and_repair": True,
        "scope_note": (
            "Replication of E13 on 360 paired candidates. Synthetic Python benchmark; "
            "statistical intervals apply to this benchmark sampling process only."
        ),
    }

    print(json.dumps({"summary": summary, "cases": rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
