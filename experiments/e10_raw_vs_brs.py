from __future__ import annotations

import json
import os
import statistics
import time
from copy import deepcopy

from brs.agentic import JSON_CODEC, generate_and_validate
from brs.builtin_profiles import make_json_profile
from brs.providers import OpenAIResponsesProvider

PROMPTS = [
    {"id":"P01","prompt":"Create a JSON object for an exercise with a string field name and an integer field repetitions. Return only JSON."},
    {"id":"P02","prompt":"Return only JSON describing a simple exercise. Include name as text and repetitions as an integer."},
    {"id":"P03","prompt":"Generate a minimal JSON object for a workout movement. Required keys: name, repetitions. repetitions must be an integer."},
    {"id":"P04","prompt":"Create only a JSON object for one exercise with name and repetitions. No commentary."},
    {"id":"P05","prompt":"Produce a valid JSON exercise artifact. name must be a string; repetitions must be an integer."},
    {"id":"P06","prompt":"Return JSON only. Make an exercise with fields name and repetitions."},
    {"id":"P07","prompt":"Generate a compact JSON exercise object. Include a textual name and integer repetitions."},
    {"id":"P08","prompt":"Create an exercise configuration in JSON with required fields name and repetitions."},
    {"id":"P09","prompt":"Output only JSON for a basic exercise. Use name:string and repetitions:int."},
    {"id":"P10","prompt":"Make a JSON object representing one exercise; include name and repetitions as an integer."},
]

RUNS_PER_PROMPT = 5


def oracle(artifact):
    if not isinstance(artifact, dict):
        return False, "not_object"
    if set(("name","repetitions")) - set(artifact):
        return False, "missing_required_field"
    if not isinstance(artifact["name"], str) or not artifact["name"].strip():
        return False, "invalid_name"
    if not isinstance(artifact["repetitions"], int):
        return False, "repetitions_not_int"
    if artifact["repetitions"] <= 0:
        return False, "repetitions_not_positive"
    return True, "valid"


def try_parse(text):
    try:
        return json.loads(text), None
    except Exception as exc:
        return None, str(exc)


def main():
    if not os.getenv("OPENAI_API_KEY"):
        raise SystemExit("OPENAI_API_KEY is not set")

    model = os.getenv("BRS_OPENAI_MODEL", "gpt-6-luna")
    provider = OpenAIResponsesProvider(model=model)

    profile = make_json_profile(
        required_keys=("name","repetitions"),
        expected_types={"name": str, "repetitions": int},
    )

    rows=[]
    total_tokens_raw=0
    total_tokens_brs=0
    raw_latencies=[]
    brs_latencies=[]

    for spec in PROMPTS:
        for run in range(1, RUNS_PER_PROMPT+1):
            case_id=f"{spec['id']}_R{run:02d}"

            t0=time.perf_counter()
            raw_resp=provider.generate(
                instructions="Follow the user's request. Return only the requested artifact.",
                input_text=spec["prompt"],
            )
            raw_latency=time.perf_counter()-t0
            raw_latencies.append(raw_latency)
            total_tokens_raw += raw_resp.total_tokens or 0

            raw_artifact, parse_error = try_parse(raw_resp.text)
            raw_valid, raw_reason = oracle(raw_artifact) if parse_error is None else (False, "parse_error")

            t1=time.perf_counter()
            brs_result=generate_and_validate(
                prompt=spec["prompt"],
                profile=profile,
                provider=provider,
                codec=JSON_CODEC,
                max_repair_iterations=1,
                allowed_repair_check_ids={"JSON_REQUIRED_FIELDS","JSON_FIELD_TYPES"},
                generation_instructions="Follow the user's request exactly.",
                repair_instructions=(
                    "Repair only listed validation failures. Preserve correct content. "
                    "Ensure name is a non-empty string and repetitions is a positive integer."
                ),
            )
            brs_latency=time.perf_counter()-t1
            brs_latencies.append(brs_latency)
            total_tokens_brs += brs_result.total_tokens or 0

            final_valid, final_reason = oracle(brs_result.validation.artifact)

            rows.append({
                "case_id": case_id,
                "prompt_id": spec["id"],
                "prompt": spec["prompt"],
                "raw": {
                    "text": raw_resp.text,
                    "artifact": raw_artifact,
                    "parse_error": parse_error,
                    "oracle_valid": raw_valid,
                    "oracle_reason": raw_reason,
                    "tokens": raw_resp.total_tokens,
                    "latency_seconds": raw_latency,
                },
                "brs": {
                    "decision": brs_result.decision.value,
                    "artifact": brs_result.validation.artifact,
                    "oracle_valid": final_valid,
                    "oracle_reason": final_reason,
                    "repair_attempts": brs_result.validation.repair_attempts,
                    "iterations": brs_result.validation.iterations,
                    "provider_calls": len(brs_result.provider_calls),
                    "tokens": brs_result.total_tokens,
                    "latency_seconds": brs_latency,
                    "failed_checks": [x.check_id for x in brs_result.validation.failed_checks],
                },
            })

    raw_valid=sum(r["raw"]["oracle_valid"] for r in rows)
    brs_valid=sum(r["brs"]["oracle_valid"] for r in rows)
    brs_release=sum(r["brs"]["decision"]=="RELEASE" for r in rows)
    brs_unsafe_release=sum(
        r["brs"]["decision"]=="RELEASE" and not r["brs"]["oracle_valid"]
        for r in rows
    )
    repairs=sum(r["brs"]["repair_attempts"] for r in rows)

    summary={
        "experiment":"E10_RAW_VS_BRS",
        "model":model,
        "total_cases":len(rows),
        "prompts":len(PROMPTS),
        "runs_per_prompt":RUNS_PER_PROMPT,
        "raw_valid":raw_valid,
        "raw_invalid":len(rows)-raw_valid,
        "raw_valid_rate":raw_valid/len(rows),
        "brs_final_valid":brs_valid,
        "brs_final_invalid":len(rows)-brs_valid,
        "brs_final_valid_rate":brs_valid/len(rows),
        "brs_release":brs_release,
        "brs_unsafe_release":brs_unsafe_release,
        "repair_attempts":repairs,
        "raw_total_tokens":total_tokens_raw,
        "brs_total_tokens":total_tokens_brs,
        "raw_mean_tokens":total_tokens_raw/len(rows),
        "brs_mean_tokens":total_tokens_brs/len(rows),
        "raw_mean_latency_seconds":statistics.mean(raw_latencies),
        "brs_mean_latency_seconds":statistics.mean(brs_latencies),
        "oracle_contract":{
            "object":True,
            "required_fields":["name","repetitions"],
            "name":"non-empty string",
            "repetitions":"positive integer",
        },
        "scope_note":(
            "Same prompt family evaluated as raw generation and as independent BRS-enabled generation. "
            "Because the provider is stochastic, paired outputs are not identical artifacts. "
            "This measures pipeline-level outcome differences, not deterministic transformation of the same raw sample."
        ),
    }

    print(json.dumps({"summary":summary,"cases":rows},ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
