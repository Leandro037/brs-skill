# E13 — Paired validation with a weaker generator model

## Status

Completed successfully on 2026-10-07.

## Design

- Generator model: `gpt-4o-mini`
- Repair model: `gpt-4o-mini`
- 18 Python coding tasks
- One generated candidate per task
- The exact same candidate was frozen, scored raw, and then passed through BRS
- Deterministic hidden tests
- One repair attempt maximum
- Full hidden-test revalidation after repair

Using the same model for generation and repair means any observed gain cannot be attributed to switching to a stronger repair model.

## Results

| Metric | Raw | BRS final |
|---|---:|---:|
| Passing cases | 16/18 | 18/18 |
| Failing cases | 2/18 | 0/18 |
| Pass rate | 88.89% | 100% |
| Absolute gain | — | +2 cases |
| Gain in percentage points | — | +11.11 pp |
| Unsafe releases | — | 0 |
| Unresolved blocks | — | 0 |

### Repair behavior

| Metric | Result |
|---|---:|
| Naturally occurring raw defects | 2 |
| Raw defects detected | 2/2 |
| Repair calls | 2 |
| Raw defects successfully repaired | 2/2 |
| Conditional repair success | 100% |
| Repair iterations allowed | 1 |

### Token usage

| Metric | Tokens |
|---|---:|
| Initial generation | 3,143 |
| Repair | 638 |
| Total with BRS repair | 3,781 |
| Repair overhead vs generation | 20.30% |

The repair overhead applies to this 18-case benchmark as a whole. Only the 2 failing cases triggered repair calls.

## Interpretation

E13 is the first paired, naturally failing benchmark in this sequence to show a measurable improvement after BRS.

The raw model passed 16 of 18 frozen hidden-test suites. BRS detected both failures, sent localized failure evidence back to the same model for one repair attempt, reran the complete validation, and finished with 18 of 18 passing cases.

No unsafe release was observed.

The observed gain was:

```text
raw: 16/18 = 88.89%
BRS: 18/18 = 100.00%
absolute improvement: +2 cases / +11.11 percentage points
```

This result is stronger than E09 because the defects were not manually injected after generation. They occurred naturally in model-generated code.

It is also stronger than E10–E12 because E13 avoids the ceiling effect and uses a paired design: BRS receives the exact same raw candidate that was scored in the baseline condition.

## What this does NOT prove

This is still a small synthetic benchmark with only 18 tasks and one model.

It does not establish:

- cross-domain generalization;
- statistical significance across repeated samples;
- superiority across model families;
- long-horizon agent reliability;
- production safety.

The 100% post-BRS pass rate should be interpreted as an observed result on this frozen benchmark, not a universal reliability estimate.

## Next validation step

A stronger follow-up should replicate E13 across:

1. multiple random runs per task;
2. at least one additional generator model;
3. a larger external benchmark;
4. confidence intervals for raw and post-BRS defect rates;
5. token/cost and latency distributions.

## Reproducibility

Workflow run:
https://github.com/Leandro037/brs-skill/actions/runs/37624834174

Artifact:
- name: `e13-weaker-model-paired-results`
- id: `11483189182`
- SHA256: `de0e56ebf7169e2cb529775b7bf75788424b8f23ef903b412c783fd56db8af1e`
