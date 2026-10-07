from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile
from typing import Any

from brs.agentic import TEXT_CODEC, with_provider_repair
from brs.factory import brs_from_profile
from brs.models import CheckResult, CheckStatus
from brs.profiles import BRSProfile
from brs.providers import OpenAIResponsesProvider


TASKS = [
    {
        "id":"T01",
        "prompt":"Write only Python code defining compress_ranges(values). values is a sorted list of unique integers. Return strings where runs of 3 or more consecutive integers use 'start-end', while runs of length 1 or 2 are emitted as separate numbers. Example: [1,2,3,5,7,8] -> ['1-3','5','7','8']. No imports.",
        "tests":[
            ("compress_ranges([1,2,3,5,7,8])",["1-3","5","7","8"]),
            ("compress_ranges([-3,-2,-1,0,2,3,4])",["-3-0","2-4"]),
            ("compress_ranges([1,2])",["1","2"]),
            ("compress_ranges([])",[]),
        ],
    },
    {
        "id":"T02",
        "prompt":"Write only Python code defining stable_mode(values). Return the most frequent value. If frequencies tie, return whichever tied value appears first in the original list. Empty input returns None. No imports.",
        "tests":[
            ("stable_mode([2,1,1,2])",2),
            ("stable_mode([3,3,2,2,1])",3),
            ("stable_mode([])",None),
            ("stable_mode(['b','a','a','b'])",'b'),
        ],
    },
    {
        "id":"T03",
        "prompt":"Write only Python code defining moving_average(values, window). Return a list of arithmetic means for every full consecutive window. If window <= 0 raise ValueError. If window > len(values), return []. No imports.",
        "tests":[
            ("moving_average([1,2,3,4],2)",[1.5,2.5,3.5]),
            ("moving_average([1,2,3],3)",[2.0]),
            ("moving_average([1,2],3)",[]),
            ("moving_average([],1)",[]),
        ],
        "raises":[("moving_average([1,2],0)","ValueError")],
    },
    {
        "id":"T04",
        "prompt":"Write only Python code defining merge_intervals(intervals). Each interval is [start,end] with start <= end. Return new merged intervals sorted by start. Intervals that overlap OR merely touch at an endpoint must merge. Do not mutate input. No imports.",
        "tests":[
            ("merge_intervals([[1,3],[3,5],[10,12]])",[[1,5],[10,12]]),
            ("merge_intervals([[5,7],[1,2],[2,4]])",[[1,4],[5,7]]),
            ("merge_intervals([])",[]),
            ("merge_intervals([[1,1],[1,1]])",[[1,1]]),
        ],
    },
    {
        "id":"T05",
        "prompt":"Write only Python code defining balanced_brackets(text). Consider only (), [], and {}. Ignore every other character. Return True only if bracket nesting/order is valid. No imports.",
        "tests":[
            ("balanced_brackets('a+(b*[c-{d}])')",True),
            ("balanced_brackets('([)]')",False),
            ("balanced_brackets('abc')",True),
            ("balanced_brackets(']')",False),
        ],
    },
    {
        "id":"T06",
        "prompt":"Write only Python code defining transpose_ragged(rows). Return the transpose of a ragged list of lists. Missing cells are filled with None. The output width equals the longest input row. Empty input returns []. No imports.",
        "tests":[
            ("transpose_ragged([[1,2,3],[4,5]])",[[1,4],[2,5],[3,None]]),
            ("transpose_ragged([[],[1,2]])",[[None,1],[None,2]]),
            ("transpose_ragged([])",[]),
            ("transpose_ragged([[1],[],[2,3]])",[[1,None,2],[None,None,3]]),
        ],
    },
    {
        "id":"T07",
        "prompt":"Write only Python code defining top_k_frequent(values, k). Return up to k distinct values sorted by descending frequency. Ties must be broken by first appearance in the original list. If k <= 0 return []. No imports.",
        "tests":[
            ("top_k_frequent([1,2,1,2,3],2)",[1,2]),
            ("top_k_frequent(['b','a','a','b','c'],2)",['b','a']),
            ("top_k_frequent([3,3,2,1,2,1],5)",[3,2,1]),
            ("top_k_frequent([1,2],0)",[]),
        ],
    },
    {
        "id":"T08",
        "prompt":"Write only Python code defining longest_streak(values). Return a tuple (value, length) for the longest consecutive run of equal values. Ties go to the earliest run. Empty input returns None. No imports.",
        "tests":[
            ("longest_streak([1,1,2,2,2,1])",(2,3)),
            ("longest_streak([1,1,2,2])",(1,2)),
            ("longest_streak([])",None),
            ("longest_streak(['a'])",('a',1)),
        ],
    },
    {
        "id":"T09",
        "prompt":"Write only Python code defining spiral(matrix). matrix is a rectangular list of lists and may be empty. Return its elements in clockwise spiral order starting at the top-left. No imports.",
        "tests":[
            ("spiral([[1,2,3],[4,5,6],[7,8,9]])",[1,2,3,6,9,8,7,4,5]),
            ("spiral([[1,2,3,4]])",[1,2,3,4]),
            ("spiral([[1],[2],[3]])",[1,2,3]),
            ("spiral([])",[]),
            ("spiral([[]])",[]),
        ],
    },
    {
        "id":"T10",
        "prompt":"Write only Python code defining longest_unique_substring(text). Return the longest substring with no repeated characters. If several have the same maximum length, return the earliest one. Empty text returns ''. No imports.",
        "tests":[
            ("longest_unique_substring('abcabcbb')",'abc'),
            ("longest_unique_substring('bbbbb')",'b'),
            ("longest_unique_substring('pwwkew')",'wke'),
            ("longest_unique_substring('abba')",'ab'),
            ("longest_unique_substring('')",''),
        ],
    },
    {
        "id":"T11",
        "prompt":"Write only Python code defining first_missing_positive(values). Return the smallest positive integer not present. Input may contain duplicates, negatives, and zero. Do not mutate input. No imports.",
        "tests":[
            ("first_missing_positive([1,2,0])",3),
            ("first_missing_positive([3,4,-1,1])",2),
            ("first_missing_positive([7,8,9,11,12])",1),
            ("first_missing_positive([1,1,2,2])",3),
            ("first_missing_positive([])",1),
        ],
    },
    {
        "id":"T12",
        "prompt":"Write only Python code defining product_except_self(values). Return a list where each element is the product of all other elements. Do not use division. No imports.",
        "tests":[
            ("product_except_self([1,2,3,4])",[24,12,8,6]),
            ("product_except_self([0,1,2,3])",[6,0,0,0]),
            ("product_except_self([0,0,2])",[0,0,0]),
            ("product_except_self([5])",[1]),
            ("product_except_self([])",[]),
        ],
    },
    {
        "id":"T13",
        "prompt":"Write only Python code defining rotate_matrix_clockwise(matrix). matrix is rectangular and may be empty. Return a new matrix rotated 90 degrees clockwise. Do not mutate input. No imports.",
        "tests":[
            ("rotate_matrix_clockwise([[1,2,3],[4,5,6]])",[[4,1],[5,2],[6,3]]),
            ("rotate_matrix_clockwise([[1],[2],[3]])",[[3,2,1]]),
            ("rotate_matrix_clockwise([[1,2,3]])",[[1],[2],[3]]),
            ("rotate_matrix_clockwise([])",[]),
            ("rotate_matrix_clockwise([[]])",[]),
        ],
    },
    {
        "id":"T14",
        "prompt":"Write only Python code defining rle_decode(items). items is a list of [value,count] pairs. count must be a non-negative integer; otherwise raise ValueError. Return the expanded list. No imports.",
        "tests":[
            ("rle_decode([['a',3],['b',1]])",['a','a','a','b']),
            ("rle_decode([[1,0],[2,2]])",[2,2]),
            ("rle_decode([])",[]),
        ],
        "raises":[
            ("rle_decode([['a',-1]])","ValueError"),
            ("rle_decode([['a',1.5]])","ValueError"),
        ],
    },
    {
        "id":"T15",
        "prompt":"Write only Python code defining nearest_pair(values). Return the pair of distinct values with smallest absolute difference as a tuple in ascending numeric order. If several pairs tie, choose the pair whose smaller value is smallest. If fewer than 2 values, return None. No imports.",
        "tests":[
            ("nearest_pair([10,2,6,4])",(2,4)),
            ("nearest_pair([1,3,5,7])",(1,3)),
            ("nearest_pair([5,5,9])",(5,5)),
            ("nearest_pair([1])",None),
            ("nearest_pair([])",None),
        ],
    },
    {
        "id":"T16",
        "prompt":"Write only Python code defining split_balanced(text). Split a string into the maximum number of non-empty parts where each part contains the same number of 'L' and 'R'. Assume the full input is balanced and contains only L and R. Return the list of parts. No imports.",
        "tests":[
            ("split_balanced('RLRRLLRLRL')",['RL','RRLL','RL','RL']),
            ("split_balanced('LLLLRRRR')",['LLLLRRRR']),
            ("split_balanced('LR')",['LR']),
            ("split_balanced('')",[]),
        ],
    },
    {
        "id":"T17",
        "prompt":"Write only Python code defining min_window_sum(values, target). Return the length of the shortest contiguous non-empty sublist whose sum is at least target. All values are positive integers. Return 0 if no such window exists. No imports.",
        "tests":[
            ("min_window_sum([2,3,1,2,4,3],7)",2),
            ("min_window_sum([1,4,4],4)",1),
            ("min_window_sum([1,1,1],5)",0),
            ("min_window_sum([5],5)",1),
            ("min_window_sum([],1)",0),
        ],
    },
    {
        "id":"T18",
        "prompt":"Write only Python code defining zigzag_rows(text, rows). Simulate writing text in zigzag across the given number of rows and return a list of row strings, not the concatenated result. If rows <= 0 raise ValueError. If rows == 1 return [text]. No imports.",
        "tests":[
            ("zigzag_rows('PAYPALISHIRING',3)",['PAHN','APLSIIG','YIR']),
            ("zigzag_rows('ABCD',2)",['AC','BD']),
            ("zigzag_rows('',3)",['','','']),
            ("zigzag_rows('A',1)",['A']),
        ],
        "raises":[("zigzag_rows('ABC',0)","ValueError")],
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
            "    try:",
            f"        observed = {expression}",
            f"        expected = {expected!r}",
            "        if observed != expected:",
            f"            failures.append({expression!r} + ' expected=' + repr(expected) + ' observed=' + repr(observed))",
            "    except Exception as exc:",
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
        return False, evidence[-1800:] if evidence else f"exit={proc.returncode}"
    except subprocess.TimeoutExpired:
        return False, "hidden tests timed out"
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass


def make_profile(task: dict[str, Any]) -> BRSProfile:
    def static_check(artifact, context):
        if not isinstance(artifact, str):
            return CheckResult(
                "CODE_STATIC_SAFE",
                CheckStatus.FAIL,
                f"expected source text, got {type(artifact).__name__}",
                repairable=True,
            )
        ok, evidence = static_safety(artifact)
        return CheckResult(
            "CODE_STATIC_SAFE",
            CheckStatus.PASS if ok else CheckStatus.FAIL,
            evidence,
            repairable=True,
        )

    def hidden_check(artifact, context):
        if not isinstance(artifact, str):
            return CheckResult(
                "CODE_HIDDEN_TESTS",
                CheckStatus.FAIL,
                "cannot execute non-text artifact",
                repairable=True,
            )
        ok, evidence = run_hidden_tests(artifact, task)
        return CheckResult(
            "CODE_HIDDEN_TESTS",
            CheckStatus.PASS if ok else CheckStatus.FAIL,
            evidence,
            repairable=True,
        )

    return BRSProfile(name=f"e13-{task['id']}", checks=[static_check, hidden_check])


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set")

    model = os.getenv("BRS_E13_MODEL", "gpt-4o-mini")
    provider = OpenAIResponsesProvider(model=model)

    rows = []
    generation_tokens = 0
    repair_tokens = 0
    repair_calls = 0

    for task in TASKS:
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
            allowed_check_ids={"CODE_STATIC_SAFE","CODE_HIDDEN_TESTS"},
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
            "case_id":task["id"],
            "prompt":task["prompt"],
            "raw":{
                "code":raw_code,
                "valid":raw_valid,
                "reason":raw_reason,
                "tokens":generated.total_tokens,
            },
            "brs":{
                "decision":result.decision.value,
                "code":result.artifact,
                "valid":final_valid,
                "reason":final_reason,
                "repair_attempts":result.repair_attempts,
                "iterations":result.iterations,
                "repair_calls":len(calls),
                "repair_tokens":case_repair_tokens,
                "failed_checks":[x.check_id for x in result.failed_checks],
            },
        })

    total=len(rows)
    raw_pass=sum(r["raw"]["valid"] for r in rows)
    raw_fail=total-raw_pass
    final_pass=sum(r["brs"]["valid"] for r in rows)
    repaired=sum((not r["raw"]["valid"]) and r["brs"]["valid"] for r in rows)
    detected=sum((not r["raw"]["valid"]) and r["brs"]["repair_attempts"]>0 for r in rows)
    unsafe_release=sum(r["brs"]["decision"]=="RELEASE" and not r["brs"]["valid"] for r in rows)
    unresolved=sum(r["brs"]["decision"]=="BLOCK" for r in rows)

    summary={
        "experiment":"E13_WEAKER_MODEL_PAIRED",
        "model":model,
        "total_cases":total,
        "raw_pass":raw_pass,
        "raw_fail":raw_fail,
        "raw_pass_rate":raw_pass/total,
        "brs_final_pass":final_pass,
        "brs_final_fail":total-final_pass,
        "brs_final_pass_rate":final_pass/total,
        "absolute_gain_cases":final_pass-raw_pass,
        "absolute_gain_rate_points":(final_pass-raw_pass)/total,
        "raw_defects_detected":detected,
        "raw_defects_repaired":repaired,
        "repair_success_rate_on_raw_defects":repaired/raw_fail if raw_fail else None,
        "unsafe_release":unsafe_release,
        "unresolved_blocks":unresolved,
        "generation_tokens":generation_tokens,
        "repair_calls":repair_calls,
        "repair_tokens":repair_tokens,
        "total_tokens_with_brs":generation_tokens+repair_tokens,
        "paired_design":True,
        "same_model_for_generation_and_repair":True,
        "scope_note":"Synthetic paired Python benchmark with deterministic hidden tests and one repair attempt.",
    }

    print(json.dumps({"summary":summary,"cases":rows},ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
