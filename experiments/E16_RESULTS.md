# E16 — Cross-model pilot with gpt-4.1-mini

## Status

Completed successfully on 2026-10-07.

## Design

- benchmark: same frozen 18 Python tasks used in E13/E14
- runs per task: 5
- total paired candidates: 90
- generation model: `gpt-4.1-mini`
- repair model: `gpt-4.1-mini`
- exact same raw candidate evaluated before BRS
- deterministic hidden tests
- maximum one repair attempt
- full revalidation after repair

## Results

| Metric | Raw | BRS final |
|---|---:|---:|
| Passing cases | 86/90 | 90/90 |
| Failing cases | 4/90 | 0/90 |
| Pass rate | 95.56% | 100.00% |
| Absolute gain | — | +4 cases |
| Gain | — | +4.44 pp |

## Paired outcomes

| Transition | Cases |
|---|---:|
| RAW FAIL → BRS PASS | 4 |
| RAW PASS → BRS FAIL | 0 |

## Detection and repair

| Metric | Result |
|---|---:|
| Raw defects | 4 |
| Raw defects detected | 4/4 |
| Raw defects repaired | 4/4 |
| Conditional repair success | 100% |
| Unsafe releases | 0 |
| Unresolved blocks | 0 |

## Token usage

| Metric | Tokens |
|---|---:|
| Initial generation | 15,462 |
| Repair | 1,309 |
| Total with BRS repair | 16,771 |
| Repair-token overhead vs generation | 8.47% |

Only the 4 failing candidates triggered repair calls.

## Task-level failures

Natural raw failures occurred in:

- `T02`: 1/5 failed raw, repaired by BRS
- `T04`: 1/5 failed raw, repaired by BRS
- `T15`: 2/5 failed raw, both repaired by BRS

All remaining task/run pairs passed raw.

## Interpretation

E16 provides a first cross-model portability signal.

Using the same frozen benchmark but switching from `gpt-4o-mini` to `gpt-4.1-mini`, the raw model achieved 95.56% and BRS raised observed functional pass rate to 100%.

The effect is smaller than E14 because the second model starts closer to ceiling, but the direction is consistent:

- natural raw failures occurred;
- BRS detected every observed failure;
- the same model repaired every observed failure from localized evidence;
- no degradation or unsafe release was observed.

## Decision

Because raw performance is already high (95.56%), this pilot does **not** justify immediately scaling to 360 cases purely for effect discovery.

A larger replication would be appropriate only if a stronger statistical estimate for this model is specifically required.

From a research-efficiency perspective, the next higher-value step is an external benchmark or a genuinely different domain/model family.

## Limitations

- 90 cases only;
- same internal 18-task benchmark;
- one model family/provider ecosystem;
- no confidence interval or significance test pre-specified for this pilot;
- no external replication.

## Reproducibility

Workflow run:
https://github.com/Leandro037/brs-skill/actions/runs/37639322463

Artifact:
- name: `e16-cross-model-pilot-results`
- artifact id: `11491396655`
- artifact ZIP SHA256: `83904fe0f69888f19f19fcd4bd409487ecf518bd5dc8542700afe714cdd49642`
