# E11 Protocol — Paired semantic validation

## Goal

Measure BRS on the **same generated candidate artifact**.

Each case follows:

1. generate once with OpenAI;
2. freeze the raw candidate;
3. score raw candidate with an external exact oracle;
4. pass that exact candidate through BRS;
5. if BRS detects a failure, allow one localized OpenAI repair;
6. revalidate the repaired artifact completely;
7. score the final artifact with the same external oracle.

## Model

`gpt-6-luna`

## Cases

30 deterministic JSON contracts.

Each expected artifact contains exactly:

- `name`
- `repetitions`
- `side`
- `tempo`

The prompt contains arithmetic, transformation, or distractor text, but the expected contract is unambiguous.

## Frozen oracle

An artifact is valid only if it exactly equals the expected dictionary for that case.

This checks both structure and semantics.

## Primary outcomes

- raw exact-valid rate;
- BRS final exact-valid rate;
- detected raw defects;
- successful repairs;
- unresolved blocks;
- unsafe releases;
- generation tokens;
- repair tokens;
- repair-call rate.

## Interpretation boundary

The prompts are synthetic and intentionally constructed to stress instruction following. E11 measures paired functional behavior on this benchmark only. It does not establish general cross-domain reliability.
