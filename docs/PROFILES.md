# Built-in Profiles

BRS Skill v1.0 includes three starter profiles.

They are examples and reusable building blocks, not claims of domain certification.

## JSON

```python
from brs.factory import brs_from_profile
from brs.builtin_profiles import make_json_profile

profile = make_json_profile(
    required_keys=("name", "repetitions"),
    expected_types={"name": str, "repetitions": int},
    defaults={"name": "untitled", "repetitions": 5},
)

brs, context = brs_from_profile(profile)
result = brs.validate({"repetitions": 5}, context=context)
```

Checks:

- artifact is a dictionary;
- required fields are present;
- configured field types match.

Missing required fields are repairable only when a default was explicitly configured.

## Code

```python
from brs.factory import brs_from_profile
from brs.builtin_profiles import make_code_profile

profile = make_code_profile(language="python")
brs, context = brs_from_profile(profile)
result = brs.validate("print('hello')", context=context)
```

The built-in code profile intentionally performs static checks only:

- non-empty source;
- Python AST parsing;
- configured placeholder markers.

It does **not** execute untrusted code and does not claim semantic correctness.

## Research document

```python
from brs.factory import brs_from_profile
from brs.builtin_profiles import make_research_document_profile

profile = make_research_document_profile(
    required_sections=("Abstract", "Method", "Results", "Limitations"),
    require_references=True,
)
brs, context = brs_from_profile(profile)
result = brs.validate(markdown_document, context=context)
```

Checks:

- non-empty Markdown text;
- required headings;
- References/Bibliography heading when configured;
- explicit Limitations or Threats to Validity section.

This profile validates document structure only. It does not verify whether scientific claims are true, references exist, statistics are correct, or the paper is publication-ready.

## Custom profiles

Use `BRSProfile` to package your own checks:

```python
from brs.profiles import BRSProfile

profile = BRSProfile(
    name="my-domain",
    checks=[check_a, check_b],
    repair=my_repair,
    safety_gate=my_gate,
)
```

Keep project-specific constraints out of the core engine.
