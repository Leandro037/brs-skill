from brs.factory import brs_from_profile
from brs.builtin_profiles import make_code_profile


profile = make_code_profile(language="python")
brs, context = brs_from_profile(profile)

source = """
def add(a, b):
    return a + b
"""

result = brs.validate(source, context=context)

print(result.decision.value)
for check in result.checks:
    print(check.check_id, check.status.value, check.evidence)
