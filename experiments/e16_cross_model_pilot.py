from __future__ import annotations

import json
import os

from brs.agentic import TEXT_CODEC, with_provider_repair
from brs.factory import brs_from_profile
from brs.providers import OpenAIResponsesProvider

from experiments.e13_weaker_model_paired import TASKS, make_profile, run_hidden_tests

RUNS_PER_TASK = 5


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set")

    model = os.getenv("BRS_E16_MODEL", "gpt-4.1-mini")
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

    total = len(rows)
    raw_pass = sum(r["raw"]["valid"] for r in rows)
    final_pass = sum(r["brs"]["valid"] for r in rows)
    raw_fail = total - raw_pass

    improved = sum((not r["raw"]["valid"]) and r["brs"]["valid"] for r in rows)
    degraded = sum(r["raw"]["valid"] and (not r["brs"]["valid"]) for r in rows)
    detected = sum((not r["raw"]["valid"]) and r["brs"]["repair_attempts"] > 0 for r in rows)
    unsafe_release = sum(r["brs"]["decision"] == "RELEASE" and not r["brs"]["valid"] for r in rows)
    unresolved = sum(r["brs"]["decision"] == "BLOCK" for r in rows)

    by_task = {}
    for task in TASKS:
        group = [r for r in rows if r["task_id"] == task["id"]]
        by_task[task["id"]] = {
            "cases": len(group),
            "raw_pass": sum(r["raw"]["valid"] for r in group),
            "brs_final_pass": sum(r["brs"]["valid"] for r in group),
            "improved": sum((not r["raw"]["valid"]) and r["brs"]["valid"] for r in group),
            "degraded": sum(r["raw"]["valid"] and (not r["brs"]["valid"]) for r in group),
            "blocks": sum(r["brs"]["decision"] == "BLOCK" for r in group),
        }

    summary = {
        "experiment": "E16_CROSS_MODEL_PILOT",
        "model": model,
        "tasks": len(TASKS),
        "runs_per_task": RUNS_PER_TASK,
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
        "unsafe_release": unsafe_release,
        "unresolved_blocks": unresolved,
        "generation_tokens": generation_tokens,
        "repair_calls": repair_calls,
        "repair_tokens": repair_tokens,
        "total_tokens_with_brs": generation_tokens + repair_tokens,
        "repair_token_overhead_fraction": repair_tokens / generation_tokens if generation_tokens else 0,
        "by_task": by_task,
        "paired_design": True,
        "same_model_for_generation_and_repair": True,
        "scope_note": "90-case cross-model pilot using the frozen E13/E14 Python benchmark.",
    }

    print(json.dumps({"summary": summary, "cases": rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
