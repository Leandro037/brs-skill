# E15-B — Paired real-world portfolio edit benchmark

## Status

Completed successfully on 2026-10-07.

## Design

- Application: E15 Portfolio Agent
- Model: `gpt-4o-mini`
- Total edit requests: 12
- Same model for generation and repair
- Same frozen raw candidate evaluated before and after BRS
- One repair attempt maximum
- Product contract safety has priority over literal compliance when the user requests a change that would break the application contract

## Main results

| Metric | Raw | BRS final |
|---|---:|---:|
| Safe-to-apply candidates | 6/12 | 11/12 |
| Unsafe candidates | 6/12 | 1/12 |
| Safe rate | 50.00% | 91.67% |
| Absolute gain | — | +5 cases |
| Gain in percentage points | — | +41.67 pp |

## Detection and repair

| Metric | Result |
|---|---:|
| Raw unsafe candidates | 6 |
| Raw unsafe candidates detected | 6/6 |
| Raw unsafe candidates repaired to safe state | 5/6 |
| Valid raw candidates degraded | 0 |
| Unresolved blocks | 1 |
| Unsafe releases | 0 |

## By category

### Safe edits

- cases: 6
- raw safe: 6/6
- BRS release: 6/6
- repairs: 0
- blocks: 0

BRS did not interfere with already-valid edits.

### Contract-breaking edits

- cases: 4
- raw safe: 0/4
- repairs attempted: 4
- BRS release after repair: 3/4
- unresolved blocks: 1

These requests explicitly asked the model to violate product invariants such as minimum project count, required sections, or minimum experience entries.

### Unsafe-link edits

- cases: 2
- raw safe: 0/2
- repairs attempted: 2
- BRS release after repair: 2/2
- unresolved blocks: 0

The raw model followed the unsafe link instructions, while BRS detected and repaired both candidates before release.

## Token usage

| Metric | Tokens |
|---|---:|
| Initial generation | 24,493 |
| Repair | 12,015 |
| Repair-token overhead vs generation | 49.05% |

This overhead is high relative to E14 because half of the 12 cases intentionally produced invalid candidates and therefore triggered repair.

## Interpretation

E15-B is the strongest real-application result so far.

The model was asked to perform realistic portfolio edits, including several requests that would degrade or break the product contract.

Without BRS, only **6 of 12** generated edit candidates were safe to apply directly.

With BRS:

- all 6 unsafe raw candidates were detected;
- 5 were repaired to a safe state;
- 1 remained blocked;
- none of the 6 already-valid candidates were degraded;
- no unsafe release was observed.

The observed safe-to-apply rate increased from **50.00% to 91.67%**.

This benchmark demonstrates a different value proposition from E14:

> BRS can act as an application-level release gate that protects product invariants even when the model follows a user instruction that would otherwise break or weaken the application.

## Important nuance

A repaired RELEASE in the contract-breaking category does not mean the model followed the user's literal request.

For these intentionally invalid requests, BRS is designed to prioritize the frozen product contract over literal compliance.

Therefore E15-B measures **safe applicability**, not unrestricted instruction-following.

## Limitations

- only 12 edit requests;
- benchmark authored within this project;
- one model;
- one application;
- no external human evaluation of copy quality;
- no repeated runs per edit request;
- no independent replication.

E15-B should be interpreted as a real-world integration benchmark, not as evidence of universal reliability.

## Reproducibility

Workflow run:
https://github.com/Leandro037/brs-skill/actions/runs/37637222493

Result artifact:
- name: `e15b-portfolio-edit-results`
- artifact id: `11491086882`
- artifact ZIP SHA256: `89bb0170f09e5bfe658bd0ae159e694e7b530757733027e133186463d6f8a2c9`
