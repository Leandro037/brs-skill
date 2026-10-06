from brs import BRS, CheckResult, CheckStatus


def required_name(artifact, context):
    ok = isinstance(artifact, dict) and bool(artifact.get("name"))
    return CheckResult(
        check_id="Q01_REQUIRED_NAME",
        status=CheckStatus.PASS if ok else CheckStatus.FAIL,
        evidence="name present" if ok else "missing required field: name",
        repairable=True,
    )


def positive_repetitions(artifact, context):
    value = artifact.get("repetitions") if isinstance(artifact, dict) else None
    ok = isinstance(value, int) and value > 0
    return CheckResult(
        check_id="Q02_POSITIVE_REPETITIONS",
        status=CheckStatus.PASS if ok else CheckStatus.FAIL,
        evidence=f"repetitions={value!r}",
        repairable=True,
    )


def repair(artifact, failed_checks, context):
    artifact = dict(artifact)
    failed_ids = {item.check_id for item in failed_checks}

    if "Q01_REQUIRED_NAME" in failed_ids:
        artifact["name"] = context.get("default_name", "untitled")

    if "Q02_POSITIVE_REPETITIONS" in failed_ids:
        artifact["repetitions"] = context.get("default_repetitions", 5)

    return artifact


if __name__ == "__main__":
    validator = BRS(
        checks=[required_name, positive_repetitions],
        repair=repair,
        max_repair_iterations=1,
    )

    candidate = {"repetitions": 0}

    result = validator.validate(
        candidate,
        context={
            "intent": "Create a named exercise with positive repetitions",
            "default_name": "lateral_raise",
            "default_repetitions": 5,
        },
    )

    print("decision:", result.decision.value)
    print("artifact:", result.artifact)
    print("repair_attempts:", result.repair_attempts)
    print("iterations:", result.iterations)
    for event in result.trace:
        print(event)
