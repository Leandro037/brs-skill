# BRS Validation Skill

## Purpose

Use BRS when an AI-generated artifact must be validated before it is accepted, released, executed, persisted, or passed to another system.

BRS is a validation protocol and orchestration skill. It is not a replacement for the generator model.

## Inputs

The skill expects:

- **artifact**: the generated object, text, configuration, code, plan, or executable specification;
- **intent**: what the user or upstream system requested;
- **constraints**: explicit rules the artifact must satisfy;
- **profile**: optional domain-specific validation profile;
- **runtime_contract**: optional execution semantics when the artifact controls runtime behavior.

## Required process

1. Normalize the user intent and explicit constraints.
2. Select the applicable atomic checks.
3. Run every mandatory check independently.
4. Record PASS/FAIL plus concise evidence for every check.
5. If all mandatory checks PASS, evaluate the final safety gate.
6. If one or more mandatory checks FAIL:
   - block release;
   - identify the failed checks;
   - perform localized repair only when permitted;
   - do not regenerate unrelated parts unless required.
7. After any repair, run the **entire mandatory check set again**.
8. Repeat only up to the configured maximum repair iterations.
9. Return RELEASE only if the final validation and safety gate pass.
10. Preserve a validation trace suitable for later review.

## Output contract

Return a structured result with:

- `decision`: `RELEASE` or `BLOCK`;
- `artifact`: final artifact version;
- `checks`: all check results;
- `failed_checks`: failed mandatory checks;
- `repair_attempts`: repairs performed;
- `iterations`: number of validation rounds;
- `trace`: structured validation events.

## Rules

- Never treat a favorable aggregate score as permission to ignore a failed mandatory check.
- Never mark a repaired artifact as valid without full revalidation.
- Never infer that multiple checks are statistically independent merely because they are separate.
- Never silently convert unavailable evidence into PASS.
- If a required check cannot run, fail closed unless the profile explicitly defines another policy.
- Do not claim runtime correctness from artifact correctness alone.
- Do not claim physical/perception correctness from synthetic runtime tests.

## Atomic check design

A good atomic check:

- evaluates one explicit property;
- returns PASS or FAIL;
- provides evidence;
- identifies whether failure is repairable;
- can be re-run deterministically or consistently;
- does not hide several unrelated judgments behind one opaque score.

Example:

```text
Q04_REQUIRED_FIELDS
Question: Are all required fields present?
PASS evidence: all required fields found
FAIL evidence: missing fields: repetitions, metric.points
```

## Recommended release hierarchy

```text
Detection
→ Defect localization
→ Repair
→ Revalidation
→ Release safety
→ Runtime conformance
→ Real-world execution
```

Success at one layer does not establish correctness at subsequent layers.

## Domain profiles

The core skill should remain domain-agnostic.

Project-specific behavior belongs in profiles, for example:

- `json`
- `code`
- `motion`
- `research`
- `documents`

A profile defines checks and optionally a repair function and safety gate.

## Failure memory

Failure memory records observed defect patterns and evidence for future system development.

It must not be represented as automatic online learning unless an actual learning mechanism exists.

Changes derived from failure memory should be versioned and evaluated prospectively.

## Example agent instruction

Before finalizing an AI-generated artifact:

1. call BRS with the artifact, intent, and profile;
2. if BRS returns BLOCK, repair only the failed constraints when possible;
3. rerun BRS after repair;
4. deliver the artifact only after RELEASE;
5. expose validation evidence when useful to the user or downstream system.
