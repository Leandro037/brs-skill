from __future__ import annotations

from copy import deepcopy
from typing import Any

from brs.models import CheckResult, CheckStatus
from brs.profiles import BRSProfile


def make_json_profile(
    *,
    required_keys: tuple[str, ...] = (),
    expected_types: dict[str, type] | None = None,
    defaults: dict[str, Any] | None = None,
) -> BRSProfile:
    """Create a simple JSON/dict validation profile.

    This profile validates Python dictionaries that represent JSON objects.
    It can repair missing required keys only when a default value was supplied.
    """

    expected_types = dict(expected_types or {})
    defaults = dict(defaults or {})

    def is_object(artifact: Any, context: dict[str, Any]) -> CheckResult:
        ok = isinstance(artifact, dict)
        return CheckResult(
            check_id="JSON_OBJECT",
            status=CheckStatus.PASS if ok else CheckStatus.FAIL,
            evidence="artifact is an object" if ok else f"expected dict, got {type(artifact).__name__}",
            repairable=False,
        )

    def required_fields(artifact: Any, context: dict[str, Any]) -> CheckResult:
        if not isinstance(artifact, dict):
            return CheckResult(
                check_id="JSON_REQUIRED_FIELDS",
                status=CheckStatus.FAIL,
                evidence="cannot inspect fields because artifact is not a dict",
                repairable=False,
            )
        missing = [key for key in required_keys if key not in artifact]
        repairable = bool(missing) and all(key in defaults for key in missing)
        return CheckResult(
            check_id="JSON_REQUIRED_FIELDS",
            status=CheckStatus.PASS if not missing else CheckStatus.FAIL,
            evidence="all required fields present" if not missing else f"missing fields: {missing}",
            repairable=repairable,
            metadata={"missing": missing},
        )

    def field_types(artifact: Any, context: dict[str, Any]) -> CheckResult:
        if not isinstance(artifact, dict):
            return CheckResult(
                check_id="JSON_FIELD_TYPES",
                status=CheckStatus.FAIL,
                evidence="cannot inspect types because artifact is not a dict",
                repairable=False,
            )
        errors = []
        for key, expected in expected_types.items():
            if key in artifact and not isinstance(artifact[key], expected):
                errors.append(f"{key}: expected {expected.__name__}, got {type(artifact[key]).__name__}")
        return CheckResult(
            check_id="JSON_FIELD_TYPES",
            status=CheckStatus.PASS if not errors else CheckStatus.FAIL,
            evidence="field types valid" if not errors else "; ".join(errors),
            repairable=False,
            metadata={"errors": errors},
        )

    def repair(artifact: Any, failed_checks: list[CheckResult], context: dict[str, Any]) -> Any:
        fixed = deepcopy(artifact)
        if not isinstance(fixed, dict):
            return fixed
        missing = []
        for result in failed_checks:
            if result.check_id == "JSON_REQUIRED_FIELDS":
                missing.extend(result.metadata.get("missing", []))
        for key in missing:
            if key in defaults:
                fixed[key] = deepcopy(defaults[key])
        return fixed

    return BRSProfile(
        name="json",
        checks=[is_object, required_fields, field_types],
        repair=repair,
    )
