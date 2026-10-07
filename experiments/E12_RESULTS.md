# E12 — Paired Python code validation with hidden tests

## Status

Completed successfully on 2026-10-07.

## Design

- Model: `gpt-6-luna`
- 12 Python coding tasks
- One frozen generated candidate per task
- Raw candidate evaluated with deterministic hidden tests
- Same candidate then passed through BRS
- One repair attempt allowed if syntax, static safety, or hidden tests failed
- Generated code executed only after rejecting imports and selected dangerous built-ins, in a short-lived subprocess with timeout

## Results

| Metric | Result |
|---|---:|
| Raw hidden-test pass | 12/12 |
| Raw hidden-test fail | 0/12 |
| Raw pass rate | 100% |
| BRS final hidden-test pass | 12/12 |
| BRS final hidden-test fail | 0/12 |
| Raw defects detected | 0 |
| Raw defects repaired | 0 |
| Unsafe releases | 0 |
| Repair calls | 0 |
| Repair tokens | 0 |
| Generation tokens | 2,476 |

## Interpretation

Moving from structured JSON to executable Python with hidden behavioral tests still did not create observable headroom: the raw model passed every frozen test suite.

BRS therefore added validation but did not improve measured correctness because no raw failures occurred.

This is useful negative evidence. It shows that evaluating BRS only on tasks already solved perfectly by the base model cannot establish a benefit.

## Reproducibility

Workflow run:
https://github.com/Leandro037/brs-skill/actions/runs/37611499493

Artifact:
- name: `e12-code-hidden-tests-results`
- id: `11477463453`
- SHA256: `343f8d32513ac5f38e28e6f9b3b23a529590bcb750d64cfdc49da09dcb4017b3`
