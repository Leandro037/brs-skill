# E17 — External HumanEval+ Mini pilot

## Status

Completed successfully on 2026-10-07.

A normalization-boundary issue was discovered in the first successful run and corrected before treating E17 as final evidence.

## External benchmark

- EvalPlus `0.3.1`
- HumanEval+ Mini
- 20 deterministically selected tasks
- model: `gpt-4o-mini`
- same model for generation and repair
- one repair attempt maximum
- exact same frozen raw candidate evaluated before and after BRS within each run
- external EvalPlus tests used as the correctness oracle

Selected task numbers:

`0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 120, 128, 136, 144, 152`

## Official normalized rerun

Workflow:
https://github.com/Leandro037/brs-skill/actions/runs/37647312052

| Metric | Raw | BRS final |
|---|---:|---:|
| Externally correct candidates | 18/20 | 19/20 |
| Externally incorrect candidates | 2/20 | 1/20 |
| Pass rate | 90.00% | 95.00% |
| Absolute gain | — | +1 case |
| Gain in percentage points | — | +5.00 pp |

## Paired outcomes

| Transition | Cases |
|---|---:|
| RAW FAIL → BRS PASS | 1 |
| RAW PASS → BRS FAIL | 0 |

## Detection, repair, and release consistency

| Metric | Result |
|---|---:|
| Raw defects | 2 |
| Raw defects detected | 2/2 |
| Raw defects repaired to external pass | 1/2 |
| Conditional repair success | 50.00% |
| Unresolved BLOCKs | 1 |
| Unsafe releases | 0 |
| BRS decision ↔ external oracle mismatches | **0** |

The corrected harness now applies the same EvalPlus sanitization step to repair outputs **before BRS revalidation** and before final external evaluation.

As a result, BRS release state and the external oracle agree on all 20 cases.

## Root cause of the earlier mismatch

The first successful E17 run used two slightly different artifact boundaries:

1. the BRS engine revalidated the raw repair-model text;
2. the post-cycle external evaluation applied EvalPlus `sanitize()` before testing it.

Therefore a repair response containing formatting or extra generation structure could remain `BLOCK` inside BRS while the later sanitized representation passed EvalPlus.

This was a **harness normalization inconsistency**, not evidence that the BRS engine intentionally released or rejected a different oracle result.

The fix uses a task-specific `ArtifactCodec` whose parser calls the same EvalPlus sanitizer. Repair-model output is therefore normalized before the mandatory BRS revalidation.

A regression test was added to verify that custom codec normalization is applied to repaired output before revalidation.

## Pre-fix diagnostic run

The earlier run:

https://github.com/Leandro037/brs-skill/actions/runs/37644827586

observed:

- raw external pass: 17/20 (85%)
- final external pass: 19/20 (95%)
- 2 RAW FAIL → BRS PASS
- 0 degradations
- 0 unsafe releases
- but 2 decision/external correctness mismatches

Because of that mismatch, this run is retained as **diagnostic evidence only** and is not the primary E17 result.

The raw candidate counts also differ from the corrected rerun because the model was called again; generation is not deterministic across runs.

## Token usage — official normalized rerun

| Metric | Tokens |
|---|---:|
| Initial generation | 4,963 |
| Repair | 1,113 |
| Total | 6,076 |
| Repair-token overhead | 22.43% |
| Repair calls | 2 |

## Interpretation

E17 is the first BRS experiment in which the task set and correctness oracle are external to this project.

In the corrected normalized run:

- raw `gpt-4o-mini` passed 18/20;
- BRS detected both observed raw failures;
- 1 of the 2 failures was repaired sufficiently to pass the complete external EvalPlus evaluation;
- no previously correct candidate was degraded;
- no unsafe release was observed;
- BRS decision state matched the external oracle in all 20 cases;
- externally measured pass rate increased from 90% to 95%.

This is a positive but small external-benchmark portability signal.

## Important methodological boundary

E17 is a **test-feedback repair** experiment.

BRS receives the public task specification plus localized evidence from failing EvalPlus tests. Therefore this is not comparable to zero-feedback pass@1.

The appropriate claim is:

> Given a frozen candidate and localized feedback from an external evaluator, BRS improved observed external correctness from 18/20 to 19/20 on the corrected HumanEval+ Mini pilot, with no observed degradations, unsafe releases, or release/oracle mismatches.

## Limitations

- only 20 of the 164 HumanEval tasks;
- HumanEval is widely known and may appear in model training data;
- one OpenAI model;
- one repair attempt;
- localized failing-test evidence is exposed to the repair model;
- no independent third-party replication;
- generation was re-run after fixing the harness, so the corrected run contains a new stochastic sample of candidates.

## Reproducibility

Official normalized workflow run:
https://github.com/Leandro037/brs-skill/actions/runs/37647312052

Artifact:
- name: `e17-evalplus-recovery-results`
- artifact id: `11495475289`
- artifact ZIP SHA256: `e3f0e39ef10913c3400f7591e61c0cabfeed0e93203b011405c18a96aa18de0f`
