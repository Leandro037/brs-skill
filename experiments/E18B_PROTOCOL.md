# E18-B Protocol — Official BFCL checker pilot

## Goal

Re-evaluate the E18 tool-calling hypothesis using BFCL's own scoring code instead of the internal label adapter.

## External evaluator

Pinned upstream source:

- repository: `ShishirPatil/gorilla`
- BFCL package: `berkeley-function-call-leaderboard`
- commit: `6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`

E18-B calls BFCL's official evaluation helpers directly:

- `_evaluate_single_ast_entry` / `ast_checker` for `simple_python` and `multiple`;
- `_evaluate_single_relevance_entry` for `irrelevance`.

This removes the internal exact-match oracle used in E18.

## Model

- generation: `gpt-4o-mini`
- repair: `gpt-4o-mini`

The same model is used for generation and repair.

The BFCL evaluator uses its registered OpenAI FC handler
`gpt-4o-mini-2024-07-18-FC` only to decode/normalize the structured call into the representation expected by the official checker. No BFCL inference call is made.

## Sample

Same E18 design:

- 10 deterministic spaced `simple_python` cases;
- 10 deterministic spaced `multiple` cases;
- 10 deterministic spaced `irrelevance` cases;
- 30 total candidates.

## Paired design

For each case:

1. load public BFCL v4 prompt/function data and ground truth;
2. generate one structured JSON candidate;
3. freeze the candidate;
4. score RAW with the official BFCL checker;
5. pass the exact same candidate to BRS;
6. if BFCL reports failure, allow one repair;
7. fully re-score with the same official BFCL checker;
8. record RELEASE/BLOCK and official correctness.

## Artifact bridge

BRS continues to use the portable artifact:

```json
{"calls":[{"name":"...","arguments":{}}]}
```

Before official scoring, E18-B converts that artifact into the OpenAI-FC wire representation BFCL's registered handler expects.

For OpenAI FC compatibility, dotted BFCL function names are converted to underscores exactly as BFCL's OpenAI model configuration specifies.

The bridge changes serialization only; BFCL still determines correctness.

## Repair evidence

When BFCL rejects a candidate, the repair step receives:

- the user request;
- the available BFCL function schemas;
- the official BFCL error/error type.

No project-authored expected answer is used as an oracle.

## Primary outcomes

- RAW official-BFCL pass rate;
- BRS final official-BFCL pass rate;
- RAW FAIL → BRS PASS;
- RAW PASS → BRS FAIL;
- detected defects;
- repair success;
- unresolved BLOCKs;
- unsafe releases;
- RELEASE/BLOCK ↔ BFCL mismatch;
- token overhead.

## Boundary

This is a 30-case partial BFCL evaluation with validator feedback. It is not a zero-feedback leaderboard submission and should not be compared directly with BFCL full-leaderboard overall accuracy.
