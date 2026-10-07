# E15-B Protocol — Paired real-world portfolio edit benchmark

## Goal

Evaluate BRS on real user-facing portfolio edits rather than synthetic JSON defects.

Each edit request is sent once to the model. The resulting candidate is frozen and evaluated in two ways:

1. **RAW** — would the candidate be safe to apply directly?
2. **BRS** — the exact same candidate is validated, optionally repaired once, fully revalidated, and then RELEASE/BLOCK is recorded.

## Artifact

The E15 professional portfolio JSON rendered by the Portfolio Agent.

## Model

- generation: `gpt-4o-mini`
- repair: `gpt-4o-mini`

The same model is used for generation and repair.

## Cases

The suite contains three classes:

- **safe edits** — legitimate copy/content changes that should preserve the portfolio contract;
- **contract-breaking edits** — requests that ask the model to remove required structure or reduce required collections below product minimums;
- **unsafe-link edits** — requests that would introduce non-http(s) URLs.

## Frozen release oracle

A candidate is safe to apply only if it satisfies the same mandatory portfolio contract used by the live E15 application.

The benchmark reports both:

- structural/product safety according to the frozen portfolio contract;
- whether the requested literal edit was achieved when the case defines one.

For intentionally contract-breaking requests, preserving the product contract takes priority over literal compliance.

## Primary outcomes

- raw safe-to-apply rate;
- BRS RELEASE rate;
- raw unsafe candidates detected;
- raw unsafe candidates repaired;
- unresolved BLOCKs;
- unsafe releases;
- valid raw candidates degraded by BRS;
- generation and repair token usage.

## Research boundary

E15-B measures a real application contract, but the edit suite is authored within this project and remains small. It does not establish general cross-domain reliability.
