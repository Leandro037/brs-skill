from brs.factory import brs_from_profile
from brs.builtin_profiles import make_json_profile


profile = make_json_profile(
    required_keys=("name", "repetitions"),
    expected_types={"name": str, "repetitions": int},
    defaults={"name": "untitled", "repetitions": 5},
)

brs, context = brs_from_profile(profile, max_repair_iterations=1)

candidate = {"repetitions": 3}
result = brs.validate(candidate, context=context)

print(result.decision.value)
print(result.artifact)
print([event.event for event in result.trace])
