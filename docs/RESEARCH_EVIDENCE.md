# BRS Research Evidence — v1.0 Research Release

## Scope

This document consolidates the principal experimental evidence for Binary Review Swarm (BRS) through E18-B.

BRS is a validation-and-release architecture for AI-generated artifacts:

```text
Generate
  ↓
Validate with atomic checks
  ↓
PASS ───────────────→ Release gate
FAIL
  ↓
Localized repair
  ↓
Full revalidation
  ↓
RELEASE / BLOCK
```

The results below support a **cross-context reliability signal**. They do not establish universal superiority, certification, or guaranteed safety.

## Main results

| Experiment | Domain / evaluator | Cases | RAW | BRS final | Absolute gain |
|---|---|---:|---:|---:|---:|
| E14 | Internal Python benchmark | 360 | 85.56% | 96.39% | +10.83 pp |
| E15-B | Real Portfolio Agent edits | 12 | 50.00% | 91.67% | +41.67 pp |
| E16 | Cross-model Python pilot (`gpt-4.1-mini`) | 90 | 95.56% | 100.00% | +4.44 pp |
| E17 | EvalPlus HumanEval+ Mini | 20 | 90.00% | 95.00% | +5.00 pp |
| E18-B | BFCL v4, official checker kernel | 30 | 76.67% | 90.00% | +13.33 pp |

Across these highlighted experiments, no RAW-correct candidate was observed to become incorrect after BRS in the paired evaluation, and no unsafe RELEASE was observed under the experiment oracle. These are empirical observations for the tested samples, not guarantees for future deployments.

## E14 — internal paired Python replication

- 18 tasks × 20 runs = 360 paired candidates.
- Same frozen RAW candidate evaluated before and after BRS.
- Generation and repair: `gpt-4o-mini`.
- RAW: 308/360 = 85.56%.
- BRS final: 347/360 = 96.39%.
- RAW FAIL → BRS PASS: 39.
- RAW PASS → BRS FAIL: 0.
- Observed defects detected: 52/52.
- Repaired: 39/52 = 75%.
- Unsafe releases: 0.
- McNemar p ≈ 3.64×10⁻¹².
- Bootstrap 95% interval for absolute improvement: approximately +7.78 to +14.17 percentage points.
- Repair-token overhead: approximately 23.79%.

Interpretation: strong internal paired evidence that localized repair plus mandatory revalidation can improve functional correctness when the base model has measurable headroom.

## E15-B — real application edits

Application: the BRS Portfolio Agent.

- 12 realistic editing requests.
- RAW safe-to-apply: 6/12 = 50.00%.
- BRS final safe-to-apply: 11/12 = 91.67%.
- RAW unsafe candidates detected: 6/6.
- Repaired to a safe state: 5/6.
- Valid RAW candidates degraded: 0.
- Unresolved BLOCKs: 1.
- Unsafe releases: 0.
- Repair-token overhead: approximately 49.05%.

The test set intentionally included:
- normal copy/content edits;
- requests that would violate product invariants;
- unsafe link changes.

Interpretation: BRS can act as an application-level release gate, not only as a code validator.

See [E15-B results](../experiments/E15B_RESULTS.md).

## E16 — cross-model pilot

Model: `gpt-4.1-mini`.

- 18 tasks × 5 runs = 90 paired candidates.
- RAW: 86/90 = 95.56%.
- BRS final: 90/90 = 100%.
- RAW FAIL → BRS PASS: 4.
- RAW PASS → BRS FAIL: 0.
- Defects detected: 4/4.
- Repaired: 4/4.
- Unsafe releases: 0.
- Repair-token overhead: approximately 8.47%.

Interpretation: a positive cross-model signal, although the model was already close to ceiling.

See [E16 results](../experiments/E16_RESULTS.md).

## E17 — external code benchmark

External benchmark:
- EvalPlus 0.3.1.
- HumanEval+ Mini.
- 20 selected tasks.
- Generation and repair: `gpt-4o-mini`.

Official normalized rerun:
- RAW: 18/20 = 90%.
- BRS final: 19/20 = 95%.
- RAW FAIL → BRS PASS: 1.
- RAW PASS → BRS FAIL: 0.
- Defects detected: 2/2.
- Unresolved BLOCKs: 1.
- Unsafe releases: 0.
- BRS decision ↔ external oracle mismatch: 0.
- Repair-token overhead: approximately 22.43%.

A normalization-boundary inconsistency discovered during development was corrected before the final E17 result was accepted. The earlier run is retained as diagnostic evidence only.

Interpretation: a small but positive external-benchmark signal using an evaluator outside this project.

See [E17 results](../experiments/E17_RESULTS.md).

## E18-B — external tool-calling benchmark

External benchmark:
- Berkeley Function Calling Leaderboard (BFCL) v4.
- Official BFCL checker code pinned to upstream commit `6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`.
- 30 cases: 10 `simple_python`, 10 `multiple`, 10 `irrelevance`.
- Generation and repair: `gpt-4o-mini`.

Results:
- RAW: 23/30 = 76.67%.
- BRS final: 27/30 = 90.00%.
- RAW FAIL → BRS PASS: 4.
- RAW PASS → BRS FAIL: 0.
- Defects detected: 7/7.
- Repaired: 4/7.
- Unresolved BLOCKs: 3.
- Unsafe releases: 0.
- BRS decision ↔ official BFCL checker mismatch: 0.
- Repair-token overhead: approximately 29.02%.

By category:
- `simple_python`: 9/10 → 10/10.
- `multiple`: 9/10 → 10/10.
- `irrelevance`: 5/10 → 7/10.

Interpretation: the strongest current non-code/tool-use result because correctness is determined by BFCL's own checker kernel rather than a project-authored scoring adapter.

See [E18-B results](../experiments/E18B_RESULTS.md).

## Negative and ceiling results matter

The research program also includes experiments where BRS did not improve observed outcomes because the base model already achieved ceiling or near-ceiling performance.

These runs are important: BRS should not be described as a mechanism that automatically improves every model or every task.

A more defensible interpretation is:

> BRS provides a structured reliability layer that can detect explicit failures, localize evidence, attempt bounded repair, and require full revalidation before release. Its measurable benefit depends on the validator quality, task, model, repairability of observed failures, and available headroom.

## Methodological lessons

Several implementation issues were discovered during the research and corrected rather than hidden:

1. **Normalization must be identical at validation boundaries.**  
   E17 exposed a mismatch where repaired output was sanitized for the external evaluator after BRS had already made its decision. The harness was corrected and rerun.

2. **External labels must be interpreted according to their native semantics.**  
   The first E18 BFCL adapter mishandled optional/default alternatives. That run was invalidated; regression tests were added and the experiment was rerun.

3. **Project-authored scoring can overestimate effects.**  
   E18's internal adapter produced a larger gain than E18-B. The official BFCL checker yielded the more conservative 76.67% → 90.00% result and is the preferred tool-calling evidence.

## What v1.0 supports

The experimental record supports describing BRS as:

- a reusable validation/revalidation architecture;
- provider-agnostic at the core;
- compatible with deterministic checks and external evaluators;
- capable of bounded model-based repair;
- applicable to code, structured artifacts, application edits, and tool-call decisions in the tested settings;
- empirically associated with fewer observed defect escapes in several paired experiments.

## What v1.0 does not establish

The evidence does **not** establish:

- universal generalization;
- guaranteed safety;
- independence between checks;
- superiority for every model or task;
- production certification;
- clinical, legal, financial, or safety-critical approval;
- independence from benchmark contamination;
- independent third-party replication.

## Next research milestone

The preferred next milestone is **external replication** rather than additional project-authored benchmarks.

See [External Validation Guide](./EXTERNAL_VALIDATION.md).
