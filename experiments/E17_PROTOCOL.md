# E17 Protocol — External HumanEval+ Mini pilot

## Goal

Test BRS on an externally maintained benchmark rather than project-authored tasks.

## External benchmark

E17 uses **HumanEval+ Mini** from the EvalPlus project.

EvalPlus extends HumanEval with substantially more tests and provides a reduced Mini suite intended to preserve much of the stronger evaluation signal at lower execution cost.

## Model

- generation: `gpt-4o-mini`
- repair: `gpt-4o-mini`

The same model is used for generation and repair.

## Sample

20 HumanEval+ tasks, deterministically distributed across the benchmark:

`0, 8, 16, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 120, 128, 136, 144, 152`

One generated candidate per task.

## Paired design

For every task:

1. load the external HumanEval+ Mini task and oracle;
2. generate one candidate;
3. apply EvalPlus code sanitization;
4. freeze the candidate;
5. evaluate RAW using EvalPlus base + plus tests;
6. pass the exact same frozen candidate to BRS;
7. if EvalPlus reports failure, allow one localized repair;
8. run the same EvalPlus evaluator again;
9. record RELEASE/BLOCK and raw/final correctness.

## External oracle

A candidate passes only if it passes both:

- HumanEval base tests;
- HumanEval+ Mini additional tests.

The BRS check delegates correctness to EvalPlus.

## Repair evidence

When a candidate fails, BRS receives:

- the public task specification;
- base/plus status;
- number of failed external tests;
- at most one failing external input and expected output from each failing suite.

This makes E17 a **test-feedback repair** experiment. It is not a zero-feedback pass@1 benchmark.

## Primary outcomes

- raw external pass rate;
- post-BRS external pass rate;
- RAW FAIL → BRS PASS;
- RAW PASS → BRS FAIL;
- defect detection;
- repair success;
- unresolved BLOCKs;
- unsafe releases;
- token overhead.

## Important limitations

- only 20 of 164 HumanEval tasks;
- HumanEval is a widely known benchmark and may be present in model training data;
- one provider/model;
- one repair attempt;
- repair receives localized failing-test evidence;
- this is an external-benchmark pilot, not an independent third-party replication.
