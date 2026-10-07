# E11 — Paired semantic JSON validation

## Status

Completed successfully on 2026-10-07.

## Design

- Model: `gpt-6-luna`
- 30 paired cases
- One generated candidate per case
- The same frozen candidate was scored raw and then passed through BRS
- Exact-value oracle over four fields: `name`, `repetitions`, `side`, `tempo`

## Results

| Metric | Result |
|---|---:|
| Raw exact-valid | 30/30 |
| Raw exact-invalid | 0/30 |
| BRS final exact-valid | 30/30 |
| BRS unsafe releases | 0 |
| Raw defects detected for repair | 0 |
| Repair calls | 0 |
| Repair tokens | 0 |
| Generation tokens | 4,306 |

## Interpretation

E11 corrected the pairing limitation of E10: every candidate was generated once and then frozen before BRS evaluation.

However, the raw model again achieved 100% exact validity. Therefore BRS had no defects to detect or repair.

This is another ceiling-effect result and does not support a claim of quality improvement on this benchmark.

## Reproducibility

Workflow run:
https://github.com/Leandro037/brs-skill/actions/runs/37611121490

Artifact:
- name: `e11-paired-semantic-results`
- id: `11478097070`
- SHA256: `0503d30d8dcfc0303cd683aa3248d74d472c2947c95bbf483734207c43f4a391`
