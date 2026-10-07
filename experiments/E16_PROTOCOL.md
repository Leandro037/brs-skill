# E16 Protocol — Cross-model pilot

## Goal

Test whether the paired BRS effect observed with gpt-4o-mini transfers to a second OpenAI model.

## Model

- generation: `gpt-4.1-mini`
- repair: `gpt-4.1-mini`

The same model is used for generation and repair.

## Benchmark

- same frozen 18 Python tasks used in E13/E14;
- 5 runs per task;
- 90 paired candidates total;
- exact raw candidate frozen before BRS;
- deterministic hidden tests;
- maximum one repair attempt;
- full revalidation after repair.

## Outcomes

- raw pass rate;
- final BRS pass rate;
- RAW FAIL → BRS PASS;
- RAW PASS → BRS FAIL;
- defect detection;
- repair success;
- unresolved blocks;
- unsafe releases;
- generation and repair token usage.

## Decision rule

This is a pilot. If it shows meaningful non-ceiling headroom and a positive paired effect, a larger replication can be justified. If the raw model is already near 100%, we stop rather than spend more API budget.

## Boundary

This is still an internal synthetic benchmark. It tests cross-model portability on one task family, not generality across domains.
