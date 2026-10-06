# Changelog

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
