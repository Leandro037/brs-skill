# E17 — External HumanEval+ Mini pilot

## Status

Completed successfully on 2026-10-07.

## External benchmark

- EvalPlus `0.3.1`
- HumanEval+ Mini
- 20 deterministically selected tasks
- model: `gpt-4o-mini`
- same model for generation and repair
- one repair attempt maximum
- exact same frozen raw candidate evaluated before and after BRS
- external EvalPlus tests used as the correctness oracle

Selected task numbers:

`0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 120, 128, 136, 144, 152`

## Main results

| Metric | Raw | BRS final |
|---|---:|---:|
| Externally correct candidates | 17/20 | 19/20 |
| Externally incorrect candidates | 3/20 | 1/20 |
| Pass rate | 85.00% | 95.00% |
| Absolute gain | — | +2 cases |
| Gain in percentage points | — | +10.00 pp |

## Paired outcomes

| Transition | Cases |
|---|---:|
| RAW FAIL → BRS PASS | 2 |
| RAW PASS → BRS FAIL | 0 |

## Detection and repair

| Metric | Result |
|---|---:|
| Raw defects | 3 |
| Raw defects detected | 3/3 |
| Raw defects repaired to external pass | 2/3 |
| Conditional repair success | 66.67% |
| Unsafe releases | 0 |
| Final external failures | 1 |

## Decision-state nuance

The run reports `unresolved_blocks = 3` while external final correctness reports only `1` failing artifact.

This means the experiment currently distinguishes two different outcomes:

1. **BRS engine decision state** — whether the validation/repair cycle returned RELEASE or BLOCK.
2. **External final correctness** — whether the final artifact passes the complete EvalPlus oracle when evaluated after the BRS cycle.

For E17, the primary scientific outcome is the external oracle result: **19/20 final artifacts pass HumanEval+ Mini**.

The mismatch should not be silently collapsed. It indicates that the current experiment harness can retain a BLOCK decision even when a post-cycle external evaluation observes a passing repaired artifact. This is a useful implementation finding and should be investigated before using `BLOCK` counts as a direct proxy for final correctness in future external-oracle experiments.

No unsafe release was observed.

## Token usage

| Metric | Tokens |
|---|---:|
| Initial generation | 4,866 |
| Repair | 1,730 |
| Total | 6,596 |
| Repair-token overhead | 35.55% |
| Repair calls | 3 |

The relatively high percentage overhead reflects the small sample: 3 of 20 candidates triggered repair.

## Interpretation

E17 is the first BRS experiment in which the task set and correctness oracle are external to this project.

On the selected HumanEval+ Mini tasks:

- raw `gpt-4o-mini` passed 17/20;
- BRS detected all 3 observed raw failures;
- 2 of those 3 were repaired sufficiently to pass the complete external EvalPlus evaluation;
- no previously correct candidate was degraded;
- no unsafe release was observed;
- externally measured pass rate increased from 85% to 95%.

This is a positive external-benchmark portability signal.

It is stronger than the internal E13/E14 evidence with respect to benchmark independence, but much smaller in sample size.

## Important methodological boundary

E17 is a **test-feedback repair** experiment.

BRS receives the public task specification plus localized evidence from failing EvalPlus tests (including at most one failing input/expected-output example per failing suite). Therefore this is not comparable to zero-feedback pass@1.

The appropriate claim is:

> Given a frozen candidate and localized feedback from an external evaluator, BRS improved observed external correctness from 17/20 to 19/20 on this HumanEval+ Mini pilot.

## Limitations

- only 20 of the 164 HumanEval tasks;
- HumanEval is widely known and may appear in model training data;
- one OpenAI model;
- one repair attempt;
- localized failing-test evidence is exposed to the repair model;
- no independent third-party replication;
- the BRS decision-state/external-correctness mismatch needs follow-up.

## Reproducibility

Official workflow run:
https://github.com/Leandro037/brs-skill/actions/runs/37644827586

Artifact:
- name: `e17-evalplus-recovery-results`
- artifact id: `11494695870`
- artifact ZIP SHA256: `89460e7244e28b9457fb3100b3cb5faec71b443e392013b989d07f8bd574530e`
