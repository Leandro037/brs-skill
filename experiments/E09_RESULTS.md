# E09 — Controlled Batch Repair with OpenAI

## Status

Completed successfully on 2026-10-07.

This experiment evaluates BRS detection and model-assisted repair on a controlled synthetic JSON defect set.

It is **not** an external benchmark and does not establish cross-domain generalization.

## Configuration

- Model: `gpt-6-luna`
- Total cases: 60
- Valid cases: 20
- Invalid cases: 40
- Invalid categories: 4 × 10 cases
- Maximum repair iterations: 1
- Repair provider: OpenAI Responses API
- Final release decision: BRS

## Dataset

The 40 invalid cases were known in advance and split evenly across:

1. `MISSING_NAME`
2. `MISSING_REPETITIONS`
3. `REPETITIONS_WRONG_TYPE`
4. `BOTH_FIELDS_MISSING`

The 20 valid cases contained both required fields with correct configured types.

## Results

| Metric | Result |
|---|---:|
| Valid cases released at baseline | 20/20 |
| Invalid cases blocked at baseline | 40/40 |
| Baseline invalid detection rate | 100% |
| Valid cases released after repair-enabled pipeline | 20/20 |
| Invalid cases successfully repaired and released | 40/40 |
| Invalid cases remaining blocked | 0/40 |
| Conditional repair success | 100% |
| OpenAI repair calls | 40 |
| Total tokens | 5,669 |
| Mean tokens per repaired case | 141.725 |
| Median tokens per repaired case | 141 |

### By category

| Category | Cases | Baseline blocked | Post-repair released | Tokens |
|---|---:|---:|---:|---:|
| BOTH_FIELDS_MISSING | 10 | 10 | 10 | 1,403 |
| MISSING_NAME | 10 | 10 | 10 | 1,384 |
| MISSING_REPETITIONS | 10 | 10 | 10 | 1,425 |
| REPETITIONS_WRONG_TYPE | 10 | 10 | 10 | 1,457 |
| VALID | 20 | 0 | 20 | 0 |

## Interpretation

The baseline BRS profile detected all 40 seeded defects and blocked them.

When provider-assisted repair was enabled, BRS passed the localized validation evidence to OpenAI, allowed one repair attempt, and then executed the complete BRS validation again.

All 40 defective artifacts satisfied the configured JSON checks after repair and were released only after successful revalidation.

No provider call was made for the 20 artifacts that already passed validation.

This demonstrates the implemented flow:

```text
known defect
→ atomic BRS detection
→ BLOCK
→ localized model-assisted repair
→ complete BRS revalidation
→ RELEASE
```

## Important limitations

This experiment should not be described as a comparison of "AI without BRS vs AI with BRS".

The baseline condition is **BRS without repair**, not raw model generation without validation.

The defects are synthetic, simple, deterministic, and known in advance. The repair prompt explicitly describes the intended schema. Therefore the 100% repair result should be interpreted as controlled functional evidence, not a general reliability estimate.

The next stronger experiment should compare:

1. raw model generation with no BRS;
2. the same model generation followed by BRS;
3. BRS + localized repair;

using prompts whose defects are not manually injected after generation, with a frozen external oracle and preferably multiple models/domains.

## Reproducibility

Workflow run: https://github.com/Leandro037/brs-skill/actions/runs/37609937239

Result artifact:

- name: `e09-batch-repair-results`
- artifact id: `11477855330`
- SHA256: `94e626cddba17f16b04b4369d338119ecb43d3a36d70e6fb26f81301a4cdc7ea`
