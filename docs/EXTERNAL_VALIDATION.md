# External Validation Guide

## Purpose

BRS v1.0 opens the next research phase to independent users, developers, and research teams.

The goal is not to reproduce a predetermined improvement. The goal is to test whether BRS helps, has no effect, or harms performance under a clearly specified external setup.

Negative and null results are useful.

## Recommended paired design

Use the same generated candidate for both conditions:

```text
Prompt / task
     ↓
Generate once
     ↓
Freeze RAW candidate
   ↙             ↘
RAW oracle       BRS
score            validation
                    ↓
                 optional repair
                    ↓
                 full revalidation
                    ↓
                 final oracle score
```

Do **not** generate one sample for RAW and a different sample for BRS when claiming a paired effect.

## Minimum information to report

Please report:

| Field | What to provide |
|---|---|
| Domain | Code, tool calling, JSON, document, workflow, etc. |
| Dataset | Public benchmark, internal dataset, or task description |
| Dataset version/hash | When available |
| Generator model | Exact provider/model/version |
| Repair model | Exact provider/model/version |
| Candidate count | Total paired artifacts |
| Repair limit | Maximum repair iterations |
| Validator | Checks/oracle used |
| RAW pass | Count and percentage |
| BRS final pass | Count and percentage |
| RAW FAIL → BRS PASS | Paired improvements |
| RAW PASS → BRS FAIL | Paired degradations |
| BLOCKs | Final unresolved cases |
| Unsafe releases | RELEASE artifacts that fail the final oracle |
| Decision/oracle mismatches | If an external oracle exists |
| Tokens/cost | Generation and repair separately when possible |
| Runtime/latency | Optional but useful |
| Code/commit | Reproduction reference if public |

## Strongly recommended controls

1. Freeze the validation profile before evaluating the test set.
2. Freeze the candidate before comparing RAW and BRS.
3. Use an external or deterministic oracle where possible.
4. Keep repair iterations bounded.
5. Re-run the **full** mandatory validator after repair.
6. Record every unresolved BLOCK.
7. Record degradations, not only improvements.
8. Separate validator-feedback repair from zero-feedback pass@1.
9. Preserve invalid or null experiments instead of silently dropping them.
10. Version the benchmark, code, model, and evaluator.

## Suggested result schema

```json
{
  "study": "external-study-name",
  "brs_version": "1.0.0",
  "domain": "tool-calling",
  "dataset": "example benchmark",
  "generator_model": "provider/model",
  "repair_model": "provider/model",
  "cases": 100,
  "raw_pass": 72,
  "brs_final_pass": 81,
  "paired_improved": 10,
  "paired_degraded": 1,
  "unresolved_blocks": 19,
  "unsafe_releases": 0,
  "decision_oracle_mismatches": 0,
  "generation_tokens": 120000,
  "repair_tokens": 18000,
  "notes": "Repair received localized validator feedback."
}
```

## Interpreting outcomes

### Positive result

A positive result should report both improvement and failures.

Prefer:

> On 100 paired candidates, RAW passed 72 and BRS final passed 81. Ten RAW failures were repaired, one RAW-correct candidate degraded, and no unsafe release was observed.

Avoid:

> BRS makes the model 9% smarter.

### Null result

A null result is valid evidence.

Examples:
- the generator is already at ceiling;
- failures are not repairable;
- the validator does not provide useful evidence;
- BRS detects defects but cannot improve final correctness.

### Negative result

A negative result is especially valuable.

Report:
- degradations;
- false blocks;
- unsafe releases;
- oracle mismatches;
- validator failures;
- cost/latency regressions.

## External-validation issue/report template

When opening a GitHub issue or discussion, use this outline:

```text
Title: External validation — <domain> / <model> / <dataset>

BRS version:
Commit:

Domain:
Dataset:
Generator model:
Repair model:
Cases:

Validator/oracle:
Repair iterations:

RAW pass:
BRS final pass:
RAW FAIL → BRS PASS:
RAW PASS → BRS FAIL:
BLOCKs:
Unsafe releases:
Decision/oracle mismatches:

Generation tokens/cost:
Repair tokens/cost:

What worked:
What failed:
Unexpected behavior:

Reproduction link:
```

## Research boundary

An external validation does not automatically become part of the official BRS evidence set.

External results should be labeled by provenance and reviewed for:
- paired-design integrity;
- evaluator validity;
- reproducibility;
- leakage;
- benchmark contamination;
- post-hoc changes to checks.

## Where to start

If you want a minimal first test:

1. choose 20–50 tasks with an objective oracle;
2. generate each candidate once;
3. freeze it;
4. measure RAW;
5. run BRS with one bounded repair;
6. re-run the complete oracle;
7. publish every paired outcome.

If BRS is useful only in some cases, that is still a useful result.
