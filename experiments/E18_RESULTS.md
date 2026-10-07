# E18 — External BFCL tool-calling pilot

## Status

Completed successfully on 2026-10-07.

The first E18 run exposed an error in the internal BFCL label adapter: optional/default alternatives were interpreted too strictly, and the alternatives container itself could be accepted as a literal argument value. That run is diagnostic only and is not used as evidence.

The adapter was corrected, regression tests were added, and E18 was rerun. The corrected run below is the official E18 result.

## External benchmark

E18 uses public BFCL v4 data from the Berkeley Function Calling Leaderboard.

Categories:

- `simple_python`: one relevant tool, argument extraction;
- `multiple`: choose the correct tool among several;
- `irrelevance`: abstain when no available tool is appropriate.

The benchmark questions, tool schemas, and possible-answer labels are external to this project.

## Design

- model: `gpt-4o-mini`
- same model for generation and repair
- 30 total cases
- 10 deterministic spaced cases per category
- one generation per case
- exact same frozen RAW candidate passed to BRS
- one repair attempt maximum
- full revalidation after repair
- structured JSON artifact: `{"calls":[...]}`

## Official corrected result

Workflow:
https://github.com/Leandro037/brs-skill/actions/runs/37649603904

| Metric | RAW | BRS final |
|---|---:|---:|
| Correct according to BFCL-label adapter | 19/30 | 29/30 |
| Incorrect | 11/30 | 1/30 |
| Pass rate | 63.33% | 96.67% |
| Absolute gain | — | +10 cases |
| Gain in percentage points | — | +33.33 pp |

## Paired outcomes

| Transition | Cases |
|---|---:|
| RAW FAIL → BRS PASS | 10 |
| RAW PASS → BRS FAIL | 0 |

## Detection, repair, and release

| Metric | Result |
|---|---:|
| Raw defects | 11 |
| Raw defects detected | 11/11 |
| Raw defects repaired to pass | 10/11 |
| Conditional repair success | 90.91% |
| Unresolved BLOCKs | 1 |
| Unsafe releases | 0 |
| BRS decision ↔ external-label mismatch | 0 |

## By category

| Category | RAW | BRS final | Improvement |
|---|---:|---:|---:|
| simple_python | 7/10 | 9/10 | +2 |
| multiple | 8/10 | 10/10 | +2 |
| irrelevance | 4/10 | 10/10 | +6 |

No category showed a RAW PASS → BRS FAIL transition.

The largest observed effect is in `irrelevance`, where BRS corrected six inappropriate tool-call decisions to abstention.

## Token usage

| Metric | Tokens |
|---|---:|
| Initial generation | 10,792 |
| Repair | 2,584 |
| Total | 13,376 |
| Repair-token overhead | 23.94% |
| Repair calls | 11 |

Repair was adaptive: only the 11 failing RAW candidates triggered the repair model.

## Adapter correction before official rerun

The first E18 run incorrectly treated BFCL possible-answer lists such as:

`"number_of_players": ["", 10]`

as if the entire list could itself be a valid runtime argument and also required optional/default arguments to be explicitly present.

The corrected adapter now:

- interprets BFCL lists as sets of acceptable values;
- treats the empty-string sentinel as allowing omission for non-required parameters;
- rejects the alternatives container itself as a scalar runtime value;
- verifies required parameters against the supplied tool schema;
- rejects unknown/spurious argument names.

Regression tests cover both optional omission and alternative-container rejection.

Because the model was called again after the adapter fix, the corrected run is a new stochastic sample. The earlier run is retained as diagnostic evidence only.

## Interpretation

E18 is the first BRS experiment focused on **tool/function calling rather than code generation or document editing**.

On the corrected 30-case sample, BRS increased observed correctness against the external BFCL labels from 63.33% to 96.67%, with:

- all 11 observed RAW defects detected;
- 10 repaired to a passing state;
- no observed degradation of a RAW-correct candidate;
- one unresolved case correctly left BLOCKED;
- no unsafe releases;
- no decision/oracle mismatches.

This is a strong pilot signal that the BRS validation pattern can transfer to structured agent actions.

## Important methodological boundary

This is **not an official BFCL leaderboard result**.

E18 uses:

- BFCL public data;
- BFCL public function schemas;
- BFCL public possible-answer labels;

but evaluates them through an internal exact-match adapter rather than the complete official BFCL scoring CLI.

In addition, the repair model receives localized validation evidence, including accepted external-label variants when the external-label check fails. Therefore E18 is a **validator-feedback repair experiment**, not a zero-feedback function-calling benchmark.

The appropriate claim is:

> On a 30-case BFCL-v4-derived pilot evaluated by an internal adapter over BFCL public labels, BRS improved observed structured tool-call correctness from 19/30 to 29/30 with no observed degradations, unsafe releases, or release/oracle mismatches.

## Limitations

- 30 cases only;
- one model/provider;
- internal adapter rather than official BFCL CLI evaluator;
- one repair attempt;
- repair receives localized oracle feedback;
- deterministic subset but stochastic model generations;
- no independent external replication;
- BFCL benchmark exposure in model training cannot be excluded.

## Reproducibility

Official corrected workflow run:
https://github.com/Leandro037/brs-skill/actions/runs/37649603904

Artifact:
- name: `e18-bfcl-toolcall-results`
- artifact id: `11495337757`
- artifact ZIP SHA256: `530d2d96ad856594e61a08f4685caacf98430f566a0b0c6551b2bb6c00686251`

Diagnostic invalid first run:
https://github.com/Leandro037/brs-skill/actions/runs/37648937584
