# E10 Protocol — Raw Generation vs BRS Pipeline

## Goal

Compare outcome quality and resource cost between:

1. raw model generation;
2. model generation inside the BRS validation/repair pipeline.

## Frozen oracle

An artifact is valid only when:

- it is a JSON object;
- it contains `name` and `repetitions`;
- `name` is a non-empty string;
- `repetitions` is a positive integer.

The oracle is fixed before result inspection.

## Design

- 10 prompt formulations
- 5 runs per prompt
- 50 raw generations
- 50 independent BRS-pipeline generations
- model: `gpt-6-luna`

## Primary outcomes

- raw oracle-valid rate;
- BRS final oracle-valid rate;
- BRS unsafe releases;
- repair attempts;
- token usage;
- mean latency.

## Important limitation

Raw and BRS conditions are independent stochastic generations from the same prompt family. They are not the same candidate artifact before and after validation.

Therefore E10 estimates pipeline-level outcome differences. It does not isolate the causal effect of validating the exact same generated sample.

A stronger follow-up should generate each candidate once, persist it, then evaluate the identical candidate under:
- raw release;
- BRS validation only;
- BRS validation + repair.
