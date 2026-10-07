# E18-B — Official BFCL checker pilot

## Status

Completed successfully on 2026-10-07.

E18-B re-evaluates the E18 tool-calling hypothesis using BFCL's own scoring code rather than the internal label adapter used in E18.

## External evaluator

Pinned upstream source:

- repository: `ShishirPatil/gorilla`
- BFCL package: `berkeley-function-call-leaderboard`
- source commit: `6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`

Official BFCL evaluation code used:

- AST checker path for `simple_python` and `multiple`
- relevance/irrelevance checker path for `irrelevance`

The BFCL OpenAI FC handler `gpt-4o-mini-2024-07-18-FC` is used only for the serialization/decoding convention expected by BFCL. E18-B model generation and repair remain `gpt-4o-mini` through the BRS provider.

## Design

- 30 total cases
- 10 deterministic spaced `simple_python`
- 10 deterministic spaced `multiple`
- 10 deterministic spaced `irrelevance`
- one generation per case
- same frozen RAW candidate before/after BRS
- one repair attempt maximum
- official BFCL checker determines correctness
- repair receives user request, available function schemas, and official BFCL error evidence

## Official result

Workflow:
https://github.com/Leandro037/brs-skill/actions/runs/37652503782

| Metric | RAW | BRS final |
|---|---:|---:|
| Correct by official BFCL checker | 23/30 | 27/30 |
| Incorrect | 7/30 | 3/30 |
| Pass rate | 76.67% | 90.00% |
| Absolute gain | — | +4 cases |
| Gain in percentage points | — | +13.33 pp |

## Paired outcomes

| Transition | Cases |
|---|---:|
| RAW FAIL → BRS PASS | 4 |
| RAW PASS → BRS FAIL | 0 |

## Detection, repair, and release

| Metric | Result |
|---|---:|
| Raw defects | 7 |
| Raw defects detected | 7/7 |
| Raw defects repaired to official pass | 4/7 |
| Conditional repair success | 57.14% |
| Unresolved BLOCKs | 3 |
| Unsafe releases | 0 |
| BRS decision ↔ official BFCL mismatch | 0 |

## By category

| Category | RAW | BRS final | Improvement |
|---|---:|---:|---:|
| simple_python | 9/10 | 10/10 | +1 |
| multiple | 9/10 | 10/10 | +1 |
| irrelevance | 5/10 | 7/10 | +2 |

No category showed a RAW PASS → BRS FAIL transition.

## Token usage

| Metric | Tokens |
|---|---:|
| Initial generation | 10,970 |
| Repair | 3,184 |
| Total | 14,154 |
| Repair-token overhead | 29.02% |
| Repair calls | 7 |

Repair remained adaptive: only the seven RAW failures triggered the repair model.

## Interpretation

E18-B is the strongest current tool-calling result because correctness is determined by BFCL's own checker code rather than a project-authored oracle adapter.

On this 30-case partial BFCL v4 pilot:

- RAW correctness was 23/30 (76.67%);
- BRS final correctness was 27/30 (90.00%);
- four RAW failures were converted to official passes;
- no RAW-correct case was degraded;
- three unresolved cases remained BLOCKED;
- no unsafe release was observed;
- BRS RELEASE/BLOCK state agreed with the official BFCL checker on all 30 cases.

The improvement is smaller than E18's internal-adapter result (63.33% → 96.67%), which is exactly why E18-B is more useful methodologically: it removes a project-authored scoring layer and provides a more conservative estimate.

## Relationship to E18

E18 remains useful as an adapter-development and integration experiment, but E18-B should be treated as the primary evidence for BFCL-derived tool-calling claims.

E18:
- external BFCL data and labels;
- internal exact-match adapter;
- 19/30 → 29/30.

E18-B:
- same task family and paired BRS design;
- official BFCL checker code;
- 23/30 → 27/30.

The raw counts differ because the model was called again and generation is stochastic.

## Important methodological boundary

E18-B is **not a full official BFCL leaderboard submission**.

It is:

- a 30-case partial evaluation;
- scored by BFCL's official checker kernel;
- run with validator-feedback repair;
- not zero-feedback pass@1;
- not directly comparable to BFCL full-leaderboard overall accuracy.

The appropriate claim is:

> On a 30-case partial BFCL v4 pilot scored by BFCL's official checker code, BRS improved observed structured tool-call correctness from 23/30 to 27/30, with zero observed degradations, unsafe releases, or release/checker mismatches.

## Implementation note

The upstream BFCL package imports many provider integrations. The first integration attempt failed during smoke import because an unused Qwen integration expected `soundfile`. That run made no benchmark API calls and is not evidence.

The second run added the missing import dependency, passed the BFCL smoke import, and is the official E18-B run.

## Reproducibility

Official workflow run:
https://github.com/Leandro037/brs-skill/actions/runs/37652503782

Pinned BFCL source:
`6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`

Artifact:
- name: `e18b-official-bfcl-results`
- artifact id: `11497651188`
- artifact ZIP SHA256: `9046451f3e7ab70787173d813761731313d19f5b3752deb1ac740104a37181e5`

Non-evidence integration run:
https://github.com/Leandro037/brs-skill/actions/runs/37650998590
