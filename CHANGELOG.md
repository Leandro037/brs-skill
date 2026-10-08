# Changelog

## 1.0.1 — Demo privacy cleanup — 2026-10-08

### Changed

- Replaces the public Portfolio Agent demo data with a fully fictional example.
- Removes personal/professional profile data from the reusable public demo while preserving the E15/E15-B implementation, protocol, tests, and published research evidence.
- No BRS Core behavior or research result changed in this patch release.


## 1.0.0 — Research Release — 2026-10-07

### Research status

- Closes the first major internal experimental phase through E18-B.
- Consolidates paired evidence across code, application edits, cross-model evaluation, EvalPlus/HumanEval+, and BFCL tool calling.
- Adds explicit external-validation guidance for independent replication.
- Promotes E18-B, scored by BFCL's official checker kernel, as the preferred tool-calling evidence.

### Core

- Stable provider-agnostic validation/repair/revalidation/release architecture.
- Atomic binary checks with evidence.
- Bounded localized repair.
- Mandatory full revalidation.
- RELEASE/BLOCK decision.
- Validation trace and token accounting support.

### Research-integrity changes carried into v1.0

- Repair-output normalization regression coverage after E17.
- BFCL optional/default label-semantics regression coverage after E18.
- Invalid or diagnostic runs are preserved but excluded from primary evidence.

### Documentation

- Adds consolidated research evidence.
- Adds external validation guide.
- Updates citation metadata.
- Updates package and skill documentation to v1.0.

### Limitations

v1.0 is a research release, not a safety certification. Independent replication remains an open milestone.


## 0.3.0 — 2026-10-06

Adds provider-driven generation and repair, beginning with OpenAI Responses API support.

### Added

- provider-agnostic text-provider contract;
- OpenAI Responses API adapter;
- agentic generation → validation → repair → full revalidation orchestration;
- JSON and text artifact codecs;
- opt-in repair by failed check ID;
- fail-closed behavior for unparseable generation or repair output;
- provider token-usage aggregation when available;
- end-to-end OpenAI example;
- mocked integration tests that require no API key or network access;
- OpenAI setup documentation.

### Provider boundary

BRS Core remains provider-agnostic. The model proposes generation and repair; BRS checks and the safety gate determine RELEASE/BLOCK.

### Research boundary

The OpenAI adapter is implementation infrastructure. It does not by itself demonstrate that BRS improves reliability, safety, cost, or generalization across models or domains.

## 0.2.0 — 2026-10-06

Adds starter domain profiles so users can try BRS without authoring every check from scratch.

### Added

- built-in JSON profile;
- built-in Python code profile using static AST validation;
- built-in research-document Markdown profile;
- `brs_from_profile()` factory;
- three runnable profile examples;
- built-in profile tests;
- profile documentation.

### Safety boundaries

- the code profile does not execute untrusted code;
- the research-document profile validates structure, not scientific truth;
- the JSON profile repairs missing fields only when explicit defaults are configured;
- these profiles are starter implementations, not certified validators.

## 0.1.0 — 2026-10-06

Initial public implementation of BRS Skill.

### Added

- domain-agnostic BRS validation engine;
- atomic PASS/FAIL check contract;
- mandatory binary veto;
- bounded localized repair hook;
- mandatory full revalidation after repair;
- final safety-gate hook;
- structured validation trace;
- reusable skill instructions;
- JSON example;
- baseline tests.

### Research boundary

This release is derived from the BRS architecture evaluated in the original Motion Lab research program. The public skill implementation itself has not yet been independently validated across domains.
