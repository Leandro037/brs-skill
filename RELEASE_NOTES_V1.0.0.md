# BRS Skill v1.0.0 — Research Release

Released: 2026-10-07

## Summary

BRS v1.0.0 closes the first major internal experimental phase through E18-B and opens the next phase: independent external replication.

Binary Review Swarm is a provider-agnostic validation and release-safety architecture for AI-generated artifacts built around:

- atomic binary checks;
- mandatory veto;
- localized bounded repair;
- full mandatory revalidation;
- explicit RELEASE/BLOCK;
- validation traces;
- provider-independent orchestration.

## Highlighted evidence

| Experiment | Domain / evaluator | Cases | RAW | BRS final |
|---|---|---:|---:|---:|
| E14 | Internal Python benchmark | 360 | 85.56% | 96.39% |
| E15-B | Real Portfolio Agent edits | 12 | 50.00% | 91.67% |
| E16 | Cross-model Python pilot | 90 | 95.56% | 100.00% |
| E17 | EvalPlus HumanEval+ Mini | 20 | 90.00% | 95.00% |
| E18-B | BFCL v4 official checker kernel | 30 | 76.67% | 90.00% |

Across these highlighted paired experiments, no RAW-correct candidate was observed to become incorrect after BRS and no unsafe RELEASE was observed under the experiment oracle. These are empirical observations for the tested samples, not guarantees.

## Research integrity

The project preserves invalidated and diagnostic runs rather than silently dropping them.

Examples include:
- E17 repair-output normalization mismatch, corrected and rerun;
- the first E18 BFCL adapter semantics issue, invalidated and replaced;
- E18-B using BFCL's official checker kernel as the preferred tool-calling result.

## Included in v1.0.0

- consolidated research evidence;
- external validation protocol;
- updated BRS skill contract;
- updated OpenAI/provider documentation;
- updated built-in profile documentation;
- citation metadata;
- v1.0 changelog;
- package version 1.0.0.

## Research boundary

BRS v1.0.0 is a research release, not a safety certification.

It does not establish:
- universal generalization;
- guaranteed safety;
- universal superiority over alternative validation methods;
- validator infallibility;
- independent third-party replication;
- clinical, legal, financial, security, or safety-critical certification.

## Next milestone

The preferred next milestone is independent external replication.

See:
- docs/RESEARCH_EVIDENCE.md
- docs/EXTERNAL_VALIDATION.md
- CITATION.cff
- CHANGELOG.md
