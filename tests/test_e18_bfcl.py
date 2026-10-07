from experiments.e18_bfcl_toolcalls import (
    extract_ground_truth_variants,
    oracle_match,
)


def test_extract_bfcl_pair_shape():
    value = [["calculate_triangle_area", {"base": 10, "height": 5}]]
    assert extract_ground_truth_variants(value) == [
        ("calculate_triangle_area", {"base": 10, "height": 5})
    ]


def test_extract_bfcl_single_key_dict_shape():
    value = [{"math.gcd": {"num1": 40, "num2": 50}}]
    assert extract_ground_truth_variants(value) == [
        ("math.gcd", {"num1": 40, "num2": 50})
    ]


def test_simple_oracle_accepts_matching_call():
    artifact = {
        "calls": [
            {
                "name": "math.gcd",
                "arguments": {"num1": 40, "num2": 50},
            }
        ]
    }
    valid, _ = oracle_match(
        artifact,
        category="simple_python",
        variants=[("math.gcd", {"num1": 40, "num2": 50})],
    )
    assert valid


def test_irrelevance_oracle_requires_abstention():
    valid, _ = oracle_match(
        {"calls": []},
        category="irrelevance",
        variants=[],
    )
    assert valid

    invalid, _ = oracle_match(
        {"calls": [{"name": "wrong", "arguments": {}}]},
        category="irrelevance",
        variants=[],
    )
    assert not invalid
