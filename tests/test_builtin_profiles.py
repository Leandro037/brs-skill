from brs import ValidationDecision
from brs.factory import brs_from_profile
from brs.builtin_profiles import (
    make_code_profile,
    make_json_profile,
    make_research_document_profile,
)


def test_json_profile_repairs_missing_defaulted_field():
    profile = make_json_profile(
        required_keys=("name",),
        expected_types={"name": str},
        defaults={"name": "repaired"},
    )
    brs, context = brs_from_profile(profile, max_repair_iterations=1)
    result = brs.validate({}, context=context)
    assert result.decision == ValidationDecision.RELEASE
    assert result.artifact["name"] == "repaired"
    assert result.iterations == 2


def test_json_profile_blocks_wrong_type():
    profile = make_json_profile(
        required_keys=("repetitions",),
        expected_types={"repetitions": int},
    )
    brs, context = brs_from_profile(profile)
    result = brs.validate({"repetitions": "five"}, context=context)
    assert result.decision == ValidationDecision.BLOCK


def test_code_profile_accepts_valid_python():
    profile = make_code_profile()
    brs, context = brs_from_profile(profile)
    result = brs.validate("def add(a, b):\n    return a + b\n", context=context)
    assert result.decision == ValidationDecision.RELEASE


def test_code_profile_blocks_syntax_error():
    profile = make_code_profile()
    brs, context = brs_from_profile(profile)
    result = brs.validate("def broken(:\n    pass\n", context=context)
    assert result.decision == ValidationDecision.BLOCK


def test_research_document_profile_accepts_required_structure():
    profile = make_research_document_profile()
    brs, context = brs_from_profile(profile)
    document = """
# Study
## Abstract
A.
## Method
M.
## Results
R.
## Limitations
L.
## References
Ref.
"""
    result = brs.validate(document, context=context)
    assert result.decision == ValidationDecision.RELEASE


def test_research_document_profile_blocks_missing_results():
    profile = make_research_document_profile()
    brs, context = brs_from_profile(profile)
    document = """
# Study
## Abstract
A.
## Method
M.
## Limitations
L.
## References
Ref.
"""
    result = brs.validate(document, context=context)
    assert result.decision == ValidationDecision.BLOCK
