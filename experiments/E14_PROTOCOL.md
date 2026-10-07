# E14 Protocol — Replication of E13

## Goal

Replicate E13 at larger scale to estimate the stability of the observed BRS gain.

## Design

- benchmark: same 18 frozen Python tasks as E13;
- repetitions per task: 20;
- total paired candidates: 360;
- generator model: `gpt-4o-mini`;
- repair model: `gpt-4o-mini`;
- one generation per candidate;
- the exact raw candidate is frozen before BRS;
- deterministic hidden tests;
- at most one localized repair attempt;
- complete hidden-test revalidation after repair.

## Primary outcomes

- raw pass rate;
- post-BRS pass rate;
- paired improvement count (raw FAIL → BRS PASS);
- degradation count (raw PASS → BRS FAIL);
- unresolved failures;
- unsafe releases;
- conditional repair success;
- generation and repair token usage.

## Statistical summaries

E14 reports:

- 95% Wilson confidence intervals for raw and final pass rates;
- a seeded paired bootstrap 95% confidence interval for the absolute pass-rate gain;
- exact two-sided McNemar p-value from discordant pairs.

These inferential summaries describe this benchmark and sampling process only.

## Reproducibility

Randomness in the model provider is not explicitly seeded by the API. The task order and statistical bootstrap are deterministic.
