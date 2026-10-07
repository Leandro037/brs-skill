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



def test_bfcl_optional_default_may_be_omitted():
    artifact = {
        "calls": [
            {
                "name": "board_game.chess.get_top_players",
                "arguments": {"location": "New York", "minimum_rating": 2300},
            }
        ]
    }
    tools = [{
        "name": "board_game.chess.get_top_players",
        "parameters": {
            "type": "dict",
            "properties": {
                "location": {"type": "string"},
                "minimum_rating": {"type": "integer"},
                "number_of_players": {"type": "integer"},
            },
            "required": ["location", "minimum_rating"],
        },
    }]
    valid, _ = oracle_match(
        artifact,
        category="multiple",
        variants=[(
            "board_game.chess.get_top_players",
            {
                "location": ["New York", "NYC"],
                "minimum_rating": [2300],
                "number_of_players": ["", 10],
            },
        )],
        tools=tools,
    )
    assert valid


def test_bfcl_alternative_container_is_not_a_valid_scalar_value():
    artifact = {
        "calls": [
            {
                "name": "board_game.chess.get_top_players",
                "arguments": {
                    "location": ["New York", "NYC"],
                    "minimum_rating": [2300],
                    "number_of_players": ["", 10],
                },
            }
        ]
    }
    tools = [{
        "name": "board_game.chess.get_top_players",
        "parameters": {
            "type": "dict",
            "properties": {
                "location": {"type": "string"},
                "minimum_rating": {"type": "integer"},
                "number_of_players": {"type": "integer"},
            },
            "required": ["location", "minimum_rating"],
        },
    }]
    valid, _ = oracle_match(
        artifact,
        category="multiple",
        variants=[(
            "board_game.chess.get_top_players",
            {
                "location": ["New York", "NYC"],
                "minimum_rating": [2300],
                "number_of_players": ["", 10],
            },
        )],
        tools=tools,
    )
    assert not valid
