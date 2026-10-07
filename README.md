# BRS Skill

**Binary Review Swarm (BRS)** is a reusable validation skill for AI-generated structured and executable artifacts.

BRS is not a model. It is a **pre-release validation layer** that organizes explicit atomic checks, veto, localized repair, mandatory full revalidation, and a final release-safety decision.

## Status

**BRS Skill v1.0.0 — Research Release**

This repository consolidates the BRS architecture and research evidence through E18-B. Positive paired signals have been observed across code, a real application, a second model, EvalPlus/HumanEval+ Mini, and BFCL tool calling. Independent external replication remains an open milestone.

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

## Built-in profiles

BRS now includes three starter profiles:

| Profile | Purpose | Key boundary |
|---|---|---|
| `json` | Required fields and configured field types | Repairs only explicitly defaulted missing fields |
| `code-python` | Static Python source validation | Does not execute untrusted code |
| `research-document` | Structural Markdown research checks | Does not verify scientific truth or citation validity |

See [docs/PROFILES.md](./docs/PROFILES.md).

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
│   ├── profiles.py
│   ├── factory.py
│   ├── agentic.py
│   ├── providers/
│   └── builtin_profiles/
│       ├── json_profile.py
│       ├── code_profile.py
│       └── research_document_profile.py
├── docs/
│   ├── PROFILES.md
│   └── OPENAI.md
├── examples/
│   ├── json_validation.py
│   ├── use_json_profile.py
│   ├── use_code_profile.py
│   ├── use_research_document_profile.py
│   └── openai_end_to_end.py
└── tests/
    ├── test_engine.py
    └── test_builtin_profiles.py
```

## Quick start with a built-in profile

```python
from brs.factory import brs_from_profile
from brs.builtin_profiles import make_json_profile

profile = make_json_profile(
    required_keys=("name", "repetitions"),
    expected_types={"name": str, "repetitions": int},
    defaults={"name": "untitled", "repetitions": 5},
)

brs, context = brs_from_profile(profile, max_repair_iterations=1)

result = brs.validate(
    {"repetitions": 3},
    context=context,
)

print(result.decision.value)  # RELEASE
print(result.artifact)        # {'repetitions': 3, 'name': 'untitled'}
```

## Quick start with custom checks

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

## OpenAI end-to-end adapter

v0.3 adds an optional provider layer for real model generation and localized repair while keeping BRS Core provider-agnostic.

```text
Prompt
  ↓
OpenAI generation
  ↓
BRS validation
  ↓
FAIL → localized model repair
          ↓
     full revalidation
          ↓
     RELEASE / BLOCK
```

Install the optional dependency:

```bash
python -m pip install -e ".[openai]"
```

Set `OPENAI_API_KEY` in your environment and run:

```bash
python examples/openai_end_to_end.py
```

The default model is `gpt-6-luna` and can be overridden with `BRS_OPENAI_MODEL`.

See [docs/OPENAI.md](./docs/OPENAI.md) for setup and safety behavior.

## BRS Playground

BRS also includes a dependency-free web playground for trying the built-in profiles interactively.

Run:

```bash
python -m apps.brs_playground
```

Then open:

```text
http://127.0.0.1:8000
```

The playground exposes:

- JSON validation with optional default-based repair;
- static Python validation;
- research-document structure validation;
- RELEASE/BLOCK decisions;
- check-level evidence;
- repair count and validation rounds;
- final artifact and validation trace.

The Playground is a demonstration application. It does not turn the starter profiles into certified validators.

## Run the examples

```bash
python examples/use_json_profile.py
python examples/use_code_profile.py
python examples/use_research_document_profile.py
```

## Run tests

```bash
python -m pip install -e . pytest
python -m pytest
```

GitHub Actions also runs the test suite on Python 3.10, 3.11, 3.12, and 3.13.

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
