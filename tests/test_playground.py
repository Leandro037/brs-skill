from apps.brs_playground import validate_payload


def test_json_valid_release():
    result = validate_payload({
        "profile": "json",
        "artifact": '{"name":"x","repetitions":5}',
        "required_keys": ["name", "repetitions"],
        "expected_types": {"name": "str", "repetitions": "int"},
        "defaults": {"name": "untitled", "repetitions": 5},
    })
    assert result["decision"] == "RELEASE"
    assert result["repair_attempts"] == 0


def test_json_missing_name_repairs_and_releases():
    result = validate_payload({
        "profile": "json",
        "artifact": '{"repetitions":3}',
        "required_keys": ["name", "repetitions"],
        "expected_types": {"name": "str", "repetitions": "int"},
        "defaults": {"name": "untitled", "repetitions": 5},
    })
    assert result["decision"] == "RELEASE"
    assert result["artifact"]["name"] == "untitled"
    assert result["repair_attempts"] == 1
    assert result["iterations"] == 2


def test_json_wrong_type_blocks():
    result = validate_payload({
        "profile": "json",
        "artifact": '{"name":"x","repetitions":"five"}',
        "required_keys": ["name", "repetitions"],
        "expected_types": {"name": "str", "repetitions": "int"},
        "defaults": {"name": "untitled", "repetitions": 5},
    })
    assert result["decision"] == "BLOCK"
    assert "JSON_FIELD_TYPES" in result["failed_checks"]


def test_invalid_json_blocks():
    result = validate_payload({"profile": "json", "artifact": "{broken"})
    assert result["decision"] == "BLOCK"
    assert result["failed_checks"] == ["JSON_PARSE"]


def test_python_valid_release():
    result = validate_payload({
        "profile": "code",
        "artifact": "def add(a, b):\n    return a + b\n",
    })
    assert result["decision"] == "RELEASE"


def test_python_syntax_error_blocks():
    result = validate_payload({
        "profile": "code",
        "artifact": "def broken(:\n    pass\n",
    })
    assert result["decision"] == "BLOCK"
    assert "CODE_PYTHON_SYNTAX" in result["failed_checks"]


def test_research_valid_release():
    document = """# Study

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
    result = validate_payload({"profile": "research", "artifact": document})
    assert result["decision"] == "RELEASE"


def test_research_missing_results_blocks():
    document = """# Study

## Abstract
A.

## Method
M.

## Limitations
L.

## References
Ref.
"""
    result = validate_payload({"profile": "research", "artifact": document})
    assert result["decision"] == "BLOCK"
    assert "DOC_REQUIRED_SECTIONS" in result["failed_checks"]
