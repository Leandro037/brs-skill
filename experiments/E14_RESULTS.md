# E14 — Replication of E13

## Status

Execution in progress.

## Frozen design

- 18 Python tasks
- 20 runs per task
- 360 paired candidates
- generator model: `gpt-4o-mini`
- repair model: `gpt-4o-mini`
- exact same raw candidate evaluated before BRS
- deterministic hidden tests
- maximum one repair attempt
- full hidden-test revalidation after repair

## Pre-specified statistics

- raw pass rate + 95% Wilson CI
- post-BRS pass rate + 95% Wilson CI
- paired absolute gain
- paired bootstrap 95% CI for gain
- exact two-sided McNemar test
- repair success on raw defects
- unsafe releases
- unresolved blocks
- generation and repair token usage

## Interpretation rules

A positive BRS effect requires observed `RAW FAIL → BRS PASS` pairs.

`RAW PASS → BRS FAIL` pairs count as degradations and must be reported.

The statistical results apply to this frozen synthetic benchmark only and must not be generalized to all models, domains, or production settings.

## Execution note

The first GitHub Actions attempt failed before model execution because the experiment was invoked as a file and could not import the `experiments` namespace.

The workflow was corrected to run:

```bash
python -m experiments.e14_e13_replication
```

No benchmark, model, task, repair policy, or statistical criterion was changed.
