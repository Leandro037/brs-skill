# BRS Skill

**Binary Review Swarm (BRS)** is a reusable validation skill for AI-generated structured and executable artifacts.

BRS is not a model. It is a **pre-release validation layer** that organizes explicit atomic checks, veto, localized repair, mandatory full revalidation, and a final release-safety decision.

## Status

**BRS Skill v0.1 — experimental implementation**

This repository generalizes the BRS architecture beyond the original Motion Lab research domain. Cross-domain portability is a design goal and has not yet been independently validated.

## Core flow

```text
User intent / specification
        ↓
Generated artifact
        ↓
BRS atomic checks
        ↓
PASS / FAIL + evidence
   ↙               ↘
PASS               FAIL
 ↓                  ↓
Safety gate     Localized repair
 ↓                  ↓
RELEASE          Full revalidation
                    ↓
                 PASS / FAIL
```

## Why BRS?

BRS separates outcomes that are often collapsed into one metric:

- defect detection;
- defect localization;
- repair;
- revalidation;
- release safety;
- runtime conformance;
- real-world execution.

A central design principle is that **aggregate accuracy is not the same thing as release safety**.

## Repository structure

```text
brs-skill/
├── SKILL.md
├── README.md
├── LICENSE
├── pyproject.toml
├── brs/
│   ├── __init__.py
│   ├── models.py
│   ├── checks.py
│   ├── engine.py
│   └── profiles.py
├── examples/
│   └── json_validation.py
└── tests/
    └── test_engine.py
```

## Quick start

```python
from brs import BRS, CheckResult, CheckStatus

def has_name(artifact, context):
    ok = isinstance(artifact, dict) and bool(artifact.get("name"))
    return CheckResult(
        check_id="Q01_HAS_NAME",
        status=CheckStatus.PASS if ok else CheckStatus.FAIL,
        evidence="name present" if ok else "missing required field: name",
        repairable=True,
    )

brs = BRS(checks=[has_name])

result = brs.validate(
    artifact={"name": "example"},
    context={"intent": "Create a named artifact"},
)

print(result.decision)
```

## Skill usage

See [SKILL.md](./SKILL.md) for instructions intended for AI agents and model runtimes.

## Design principles

1. **Atomic validation** — one explicit property per check.
2. **Binary veto** — mandatory failed checks can block release.
3. **Localized repair** — repair targets the observed failure.
4. **Full revalidation** — repaired artifacts re-run the complete mandatory check set.
5. **Release-safety gate** — release is a separate decision.
6. **Failure trace** — failed checks and evidence remain inspectable.
7. **Domain profiles** — domain-specific checks stay outside the core engine.

## What BRS does not claim

This repository does **not** claim:

- universal accuracy;
- universal superiority over monolithic LLM judges;
- independent evaluator errors when the same model family is reused;
- validated cross-domain portability;
- clinical or safety-critical certification.

## Research origin

BRS was developed and evaluated in a research program focused on AI-generated executable movement artifacts. The experimental phase E04–E08 is treated as frozen evidence. This repository is a reusable implementation derived from that architecture, not a modification of the original experimental evidence.

## License

MIT.
