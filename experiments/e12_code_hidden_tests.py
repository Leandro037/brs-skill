from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Any

from brs.agentic import TEXT_CODEC, with_provider_repair
from brs.factory import brs_from_profile
from brs.models import CheckResult, CheckStatus
from brs.profiles import BRSProfile
from brs.providers import OpenAIResponsesProvider


TASKS = [
    {
        "id":"C01",
        "prompt":"Write only Python code defining clamp(value, low, high). If low > high, swap the bounds. Return value constrained inclusively between the bounds.",
        "function":"clamp",
        "tests":[
            ("clamp(5,0,10)",5),
            ("clamp(-2,0,10)",0),
            ("clamp(12,0,10)",10),
            ("clamp(5,10,0)",5),
            ("clamp(-3,2,-2)",-2),
        ],
    },
    {
        "id":"C02",
        "prompt":"Write only Python code defining is_palindrome(text). Ignore case and all non-alphanumeric characters. Empty normalized text counts as a palindrome.",
        "function":"is_palindrome",
        "tests":[
            ("is_palindrome('A man, a plan, a canal: Panama!')",True),
            ("is_palindrome('No lemon, no melon')",True),
            ("is_palindrome('OpenAI')",False),
            ("is_palindrome('!!!')",True),
        ],
    },
    {
        "id":"C03",
        "prompt":"Write only Python code defining dedupe(items). Return a new list preserving first-occurrence order. Items are hashable. Do not mutate the input.",
        "function":"dedupe",
        "tests":[
            ("dedupe([3,1,3,2,1])",[3,1,2]),
            ("dedupe([])",[]),
            ("dedupe(['a','a','b'])",['a','b']),
        ],
    },
    {
        "id":"C04",
        "prompt":"Write only Python code defining rotate_right(items, k). Return a new list rotated right by k positions. k may be negative or larger than the list length. Empty input returns []. Do not mutate input.",
        "function":"rotate_right",
        "tests":[
            ("rotate_right([1,2,3,4],1)",[4,1,2,3]),
            ("rotate_right([1,2,3,4],5)",[4,1,2,3]),
            ("rotate_right([1,2,3,4],-1)",[2,3,4,1]),
            ("rotate_right([],3)",[]),
        ],
    },
    {
        "id":"C05",
        "prompt":"Write only Python code defining median(values). Return the numeric median without mutating input. For an empty list, return None. For even length, return the arithmetic mean of the middle two values.",
        "function":"median",
        "tests":[
            ("median([3,1,2])",2),
            ("median([1,4,2,3])",2.5),
            ("median([])",None),
            ("median([7])",7),
        ],
    },
    {
        "id":"C06",
        "prompt":"Write only Python code defining chunk(items, size). Return consecutive chunks as lists. If size <= 0 raise ValueError. Empty input returns []. The final chunk may be shorter.",
        "function":"chunk",
        "tests":[
            ("chunk([1,2,3,4,5],2)",[[1,2],[3,4],[5]]),
            ("chunk([],3)",[]),
            ("chunk([1,2],5)",[[1,2]]),
        ],
        "raises":[("chunk([1,2],0)","ValueError"),("chunk([1],-1)","ValueError")],
    },
    {
        "id":"C07",
        "prompt":"Write only Python code defining flatten_once(items). Flatten exactly one nesting level for list elements only; non-list elements stay as-is.",
        "function":"flatten_once",
        "tests":[
            ("flatten_once([1,[2,3],4])",[1,2,3,4]),
            ("flatten_once([[1],[2,[3]]])",[1,2,[3]]),
            ("flatten_once([])",[]),
        ],
    },
    {
        "id":"C08",
        "prompt":"Write only Python code defining word_frequencies(text). Split on whitespace, lowercase each token, strip leading/trailing punctuation characters .,!?:; from each token, ignore empty tokens, and return a dict of counts.",
        "function":"word_frequencies",
        "tests":[
            ("word_frequencies('Hello, hello world!')",{"hello":2,"world":1}),
            ("word_frequencies('...Hi??? hi;')",{"hi":2}),
            ("word_frequencies('')",{}),
        ],
    },
    {
        "id":"C09",
        "prompt":"Write only Python code defining fibonacci(n). For n < 0 raise ValueError. fibonacci(0)=0 and fibonacci(1)=1. Return the nth Fibonacci number iteratively.",
        "function":"fibonacci",
        "tests":[
            ("fibonacci(0)",0),
            ("fibonacci(1)",1),
            ("fibonacci(2)",1),
            ("fibonacci(10)",55),
        ],
        "raises":[("fibonacci(-1)","ValueError")],
    },
    {
        "id":"C10",
        "prompt":"Write only Python code defining normalize_scores(values). Return [] for empty input. Otherwise linearly map min to 0.0 and max to 1.0. If all values are equal, return a list of 0.0 values of the same length.",
        "function":"normalize_scores",
        "tests":[
            ("normalize_scores([2,4,6])",[0.0,0.5,1.0]),
            ("normalize_scores([5,5])",[0.0,0.0]),
            ("normalize_scores([])",[]),
            ("normalize_scores([-2,0,2])",[0.0,0.5,1.0]),
        ],
    },
    {
        "id":"C11",
        "prompt":"Write only Python code defining pairwise_sum(values, target). Return a tuple of the indices of the first pair encountered in left-to-right nested-loop order whose values sum to target. Return None if no pair exists. Do not use the same index twice.",
        "function":"pairwise_sum",
        "tests":[
            ("pairwise_sum([2,7,11,15],9)",(0,1)),
            ("pairwise_sum([3,3,4],6)",(0,1)),
            ("pairwise_sum([1,2,3,4],7)",(2,3)),
            ("pairwise_sum([1],2)",None),
        ],
    },
    {
        "id":"C12",
        "prompt":"Write only Python code defining slugify(text). Lowercase, trim outer whitespace, replace each maximal run of non-alphanumeric characters with a single hyphen, and remove leading/trailing hyphens.",
        "function":"slugify",
        "tests":[
            ("slugify(' Hello, World! ')",'hello-world'),
            ("slugify('A__B   C')",'a-b-c'),
            ("slugify('---')",''),
            ("slugify('Café Déjà Vu')",'café-déjà-vu'),
        ],
    },
]


BANNED_CALLS = {"eval","exec","compile","open","input","__import__"}


def static_safety(code: str) -> tuple[bool, str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"syntax error line {exc.lineno}: {exc.msg}"

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return False, "imports are not allowed"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in BANNED_CALLS:
            return False, f"banned call: {node.func.id}"

    return True, "syntax and static safety passed"


def run_hidden_tests(code: str, task: dict[str, Any]) -> tuple[bool, str]:
    ok, reason = static_safety(code)
    if not ok:
        return False, reason

    lines = [code, "", "def __run_hidden_tests():", "    failures = []"]
    for expression, expected in task.get("tests", []):
        lines += [
            f"    try:",
            f"        observed = {expression}",
            f"        expected = {expected!r}",
            f"        if observed != expected:",
            f"            failures.append({expression!r} + ' expected=' + repr(expected) + ' observed=' + repr(observed))",
            f"    except Exception as exc:",
            f"        failures.append({expression!r} + ' raised ' + type(exc).__name__ + ': ' + str(exc))",
        ]
    for expression, exc_name in task.get("raises", []):
        lines += [
            "    try:",
            f"        {expression}",
            f"        failures.append({expression!r} + ' expected to raise {exc_name}')",
            f"    except {exc_name}:",
            "        pass",
            "    except Exception as exc:",
            f"        failures.append({expression!r} + ' expected {exc_name} but raised ' + type(exc).__name__)",
        ]
    lines += [
        "    if failures:",
        "        print('\\n'.join(failures))",
        "        raise SystemExit(1)",
        "if __name__ == '__main__':",
        "    __run_hidden_tests()",
    ]

    script = "\n".join(lines)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(script)
        path = f.name

    try:
        proc = subprocess.run(
            [sys.executable, "-I", path],
            capture_output=True,
            text=True,
            timeout=2.0,
        )
        if proc.returncode == 0:
            return True, "all hidden tests passed"
        evidence = (proc.stdout + "\n" + proc.stderr).strip()
        return False, evidence[-1500:] if evidence else f"exit={proc.returncode}"
    except subprocess.TimeoutExpired:
        return False, "hidden tests timed out"
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def make_profile(task: dict[str, Any]) -> BRSProfile:
    def syntax_check(artifact, context):
        if not isinstance(artifact, str):
            return CheckResult(
                "CODE_STATIC_SAFE", CheckStatus.FAIL,
                f"expected source text, got {type(artifact).__name__}", repairable=True
            )
        ok, evidence = static_safety(artifact)
        return CheckResult(
            "CODE_STATIC_SAFE",
            CheckStatus.PASS if ok else CheckStatus.FAIL,
            evidence,
            repairable=True,
        )

    def functional_check(artifact, context):
        if not isinstance(artifact, str):
            return CheckResult(
                "CODE_HIDDEN_TESTS", CheckStatus.FAIL,
                "cannot execute non-text artifact", repairable=True
            )
        ok, evidence = run_hidden_tests(artifact, task)
        return CheckResult(
            "CODE_HIDDEN_TESTS",
            CheckStatus.PASS if ok else CheckStatus.FAIL,
            evidence,
            repairable=True,
        )

    return BRSProfile(name=f"hidden-tests-{task['id']}", checks=[syntax_check, functional_check])


def raw_oracle(code: str, task: dict[str, Any]) -> tuple[bool, str]:
    return run_hidden_tests(code, task)


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set")

    model = os.getenv("BRS_OPENAI_MODEL", "gpt-6-luna")
    provider = OpenAIResponsesProvider(model=model)

    rows = []
    generation_tokens = 0
    repair_tokens = 0
    repair_calls = 0

    for task in TASKS:
        generated = provider.generate(
            instructions="Return only Python source code. Do not use Markdown fences. Do not import modules.",
            input_text=task["prompt"],
        )
        generation_tokens += generated.total_tokens or 0
        raw_code = generated.text
        raw_valid, raw_reason = raw_oracle(raw_code, task)

        calls = []
        repaired_profile = with_provider_repair(
            make_profile(task),
            provider=provider,
            codec=TEXT_CODEC,
            provider_calls=calls,
            allowed_check_ids={"CODE_STATIC_SAFE","CODE_HIDDEN_TESTS"},
            repair_instructions=(
                "Repair only the listed code failures. Return only Python source code, no Markdown. "
                "Do not import modules. Preserve correct behavior. Use the failure evidence to fix edge cases."
            ),
        )
        engine, context = brs_from_profile(repaired_profile, max_repair_iterations=1)
        result = engine.validate(raw_code, context=context)

        repair_calls += len(calls)
        case_repair_tokens = sum(call.total_tokens or 0 for call in calls)
        repair_tokens += case_repair_tokens

        final_valid, final_reason = raw_oracle(result.artifact, task)

        rows.append({
            "case_id": task["id"],
            "prompt": task["prompt"],
            "raw": {
                "code": raw_code,
                "oracle_valid": raw_valid,
                "oracle_reason": raw_reason,
                "generation_tokens": generated.total_tokens,
            },
            "brs": {
                "decision": result.decision.value,
                "code": result.artifact,
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
    raw_defects = len(rows) - raw_valid
    detected = sum((not r["raw"]["oracle_valid"]) and r["brs"]["repair_attempts"] > 0 for r in rows)
    repaired = sum((not r["raw"]["oracle_valid"]) and r["brs"]["oracle_valid"] for r in rows)
    unsafe_release = sum(r["brs"]["decision"] == "RELEASE" and not r["brs"]["oracle_valid"] for r in rows)

    summary = {
        "experiment":"E12_CODE_HIDDEN_TESTS",
        "model":model,
        "total_cases":len(rows),
        "raw_hidden_test_pass":raw_valid,
        "raw_hidden_test_fail":raw_defects,
        "raw_pass_rate":raw_valid/len(rows),
        "brs_final_hidden_test_pass":final_valid,
        "brs_final_hidden_test_fail":len(rows)-final_valid,
        "brs_final_pass_rate":final_valid/len(rows),
        "raw_defects_detected":detected,
        "raw_defects_repaired":repaired,
        "repair_success_rate_on_raw_defects":repaired/raw_defects if raw_defects else None,
        "unsafe_release":unsafe_release,
        "generation_tokens":generation_tokens,
        "repair_calls":repair_calls,
        "repair_tokens":repair_tokens,
        "mean_repair_tokens":repair_tokens/repair_calls if repair_calls else 0,
        "paired_design":True,
        "scope_note":"Paired synthetic Python benchmark with frozen hidden tests and one repair attempt.",
    }

    print(json.dumps({"summary":summary,"cases":rows},ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
