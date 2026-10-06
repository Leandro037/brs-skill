from brs.factory import brs_from_profile
from brs.builtin_profiles import make_research_document_profile


profile = make_research_document_profile(
    required_sections=("Abstract", "Method", "Results", "Limitations"),
    require_references=True,
)
brs, context = brs_from_profile(profile)

document = """
# Example study

## Abstract
Short abstract.

## Method
Method description.

## Results
Results description.

## Limitations
Internal evaluation only.

## References
- Example reference.
"""

result = brs.validate(document, context=context)

print(result.decision.value)
for check in result.checks:
    print(check.check_id, check.status.value, check.evidence)
