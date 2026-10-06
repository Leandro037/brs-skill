from brs import BRS, CheckResult, CheckStatus, ValidationDecision


def pass_check(artifact, context):
    return CheckResult("Q_PASS", CheckStatus.PASS)


def fail_check(artifact, context):
    return CheckResult(
        "Q_FAIL",
        CheckStatus.FAIL,
        evidence="forced failure",
        repairable=False,
    )


def repairable_required_field(artifact, context):
    ok = bool(artifact.get("name"))
    return CheckResult(
        "Q_NAME",
        CheckStatus.PASS if ok else CheckStatus.FAIL,
        evidence="name present" if ok else "name missing",
        repairable=True,
    )


def repair_name(artifact, failed, context):
    fixed = dict(artifact)
    fixed["name"] = "repaired"
    return fixed


def test_release_when_all_mandatory_checks_pass():
    brs = BRS([pass_check])
    result = brs.validate({"ok": True})
    assert result.decision == ValidationDecision.RELEASE
    assert result.repair_attempts == 0


def test_block_when_mandatory_check_fails():
    brs = BRS([fail_check])
    result = brs.validate({})
    assert result.decision == ValidationDecision.BLOCK
    assert [x.check_id for x in result.failed_checks] == ["Q_FAIL"]


def test_repair_requires_full_revalidation():
    brs = BRS(
        [repairable_required_field],
        repair=repair_name,
        max_repair_iterations=1,
    )
    result = brs.validate({})
    assert result.decision == ValidationDecision.RELEASE
    assert result.artifact["name"] == "repaired"
    assert result.repair_attempts == 1
    assert result.iterations == 2
