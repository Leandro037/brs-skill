# E10 — Raw model vs BRS pipeline

## Status

Completed successfully on 2026-10-07.

## Design

- Model: `gpt-6-luna`
- 10 prompt formulations
- 5 runs per prompt
- 50 raw generations
- 50 independent BRS-pipeline generations
- Fixed oracle:
  - JSON object
  - required fields `name` and `repetitions`
  - non-empty string `name`
  - positive integer `repetitions`

## Results

| Metric | Raw | BRS |
|---|---:|---:|
| Valid outputs | 50/50 | 50/50 |
| Invalid outputs | 0/50 | 0/50 |
| Valid rate | 100% | 100% |
| Unsafe releases | — | 0 |
| Repair attempts | — | 0 |
| Total tokens | 4,552 | 4,987 |
| Mean tokens/case | 91.04 | 99.74 |
| Mean latency | 1.722 s | 1.581 s |

## Interpretation

The raw model already satisfied the frozen oracle in all 50 cases. Therefore this run provides no evidence that BRS improves correctness for this prompt set.

BRS also performed no repairs because no BRS-side defect was observed.

The BRS condition consumed 435 additional tokens in aggregate, approximately 9.6% more than raw generation.

The observed mean latency was slightly lower for the BRS condition, but because the conditions are independent stochastic calls and network timing is noisy, this should not be interpreted as a latency benefit.

## Main conclusion

E10 is a **ceiling-effect result**.

The task was too easy for the selected model and oracle, so raw generation already achieved 100% validity.

This is useful negative evidence: BRS should not be claimed to improve a task when the base model already performs perfectly under the tested constraints.

## Limitation

Raw and BRS conditions were independent generations from the same prompt family. They were not the exact same candidate artifact.

A stronger follow-up should:

1. generate each artifact once;
2. persist that exact artifact;
3. score it as raw;
4. pass the same candidate through BRS;
5. repair only when BRS detects a failure;
6. re-score the exact post-BRS artifact under the same frozen oracle.

## Reproducibility

Workflow run:
https://github.com/Leandro037/brs-skill/actions/runs/37610510393

Artifact:
- name: `e10-raw-vs-brs-results`
- id: `11477641645`
- SHA256: `69caad5b2ca4811cfbf5fe1f580fb838e1039350a1169425a6ab830df93362d6`
