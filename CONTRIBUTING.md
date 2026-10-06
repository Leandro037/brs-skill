# Contributing

Thanks for contributing to BRS Skill.

## Design rule

Keep the **core engine domain-agnostic**.

Domain-specific rules should be implemented as checks or profiles rather than hard-coded into the BRS engine.

## A good contribution

A new check or profile should clearly state:

- the property being evaluated;
- what PASS means;
- what FAIL means;
- the evidence returned;
- whether the failure is repairable;
- any assumptions or unavailable evidence.

## Validation principles

Contributions should preserve these rules:

- mandatory FAIL can veto release;
- repaired artifacts undergo full revalidation;
- release is distinct from intermediate detector success;
- unavailable required evidence must not silently become PASS;
- synthetic evidence must not be presented as physical evidence;
- runtime correctness is not implied by artifact correctness.

## Tests

Please add or update tests for changes to the core engine.

Run:

```bash
python -m pytest
```
