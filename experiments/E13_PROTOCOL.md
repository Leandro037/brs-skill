# E13 Protocol — Paired validation with a weaker generator model

## Goal

Create genuine headroom for BRS by evaluating a smaller generator model on harder Python tasks while preserving a paired design.

## Model

- generation model: `gpt-4o-mini`
- repair model: `gpt-4o-mini`

Using the same model for generation and repair avoids attributing any observed gain to a stronger repair model.

## Paired design

For every task:

1. generate Python code once;
2. freeze that exact candidate;
3. evaluate the raw candidate with hidden tests;
4. pass the exact same candidate to BRS;
5. if BRS detects a failure, allow one repair attempt using the same model;
6. rerun the full hidden test suite;
7. compare raw and post-BRS behavior.

## Safety boundary

Before execution, generated code is rejected if it contains imports or selected dangerous built-ins.

Execution happens in an isolated Python subprocess with a short timeout.

## Outcomes

- raw hidden-test pass rate;
- post-BRS hidden-test pass rate;
- raw defects detected;
- repairs attempted;
- successful repairs;
- unresolved blocks;
- unsafe releases;
- generation and repair token cost.

## Interpretation

The benchmark is synthetic and deterministic. It is designed to create natural model failures rather than injecting defects after generation.

A positive result would show that validation evidence plus one repair pass can improve the same model's functional output on the same frozen candidate set.
