from __future__ import annotations

from copy import deepcopy
from typing import Any

from .checks import Check, RepairFn, SafetyGateFn
from .models import (
    CheckResult,
    CheckStatus,
    ValidationDecision,
    ValidationResult,
    ValidationTraceEvent,
)


class BRS:
    """Binary Review Swarm core validation engine.

    The engine is intentionally domain-agnostic. Domain rules belong in checks
    and profiles.
    """

    def __init__(
        self,
        checks: list[Check],
        *,
        repair: RepairFn | None = None,
        safety_gate: SafetyGateFn | None = None,
        max_repair_iterations: int = 1,
    ) -> None:
        if max_repair_iterations < 0:
            raise ValueError("max_repair_iterations must be >= 0")

        self.checks = list(checks)
        self.repair = repair
        self.safety_gate = safety_gate
        self.max_repair_iterations = max_repair_iterations

    def _run_checks(
        self,
        artifact: Any,
        context: dict[str, Any],
    ) -> list[CheckResult]:
        results: list[CheckResult] = []
        for check in self.checks:
            result = check(artifact, context)
            if not isinstance(result, CheckResult):
                raise TypeError("Every BRS check must return CheckResult")
            results.append(result)
        return results

    @staticmethod
    def _mandatory_failures(results: list[CheckResult]) -> list[CheckResult]:
        return [
            result
            for result in results
            if result.mandatory and result.status == CheckStatus.FAIL
        ]

    def validate(
        self,
        artifact: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> ValidationResult:
        context = dict(context or {})
        current = deepcopy(artifact)
        trace: list[ValidationTraceEvent] = []
        repair_attempts = 0
        iteration = 0

        while True:
            iteration += 1
            results = self._run_checks(current, context)
            failed = self._mandatory_failures(results)

            trace.append(
                ValidationTraceEvent(
                    event="validation",
                    iteration=iteration,
                    payload={
                        "failed_check_ids": [r.check_id for r in failed],
                        "check_count": len(results),
                    },
                )
            )

            if not failed:
                gate_passed = True
                if self.safety_gate is not None:
                    gate_passed = bool(self.safety_gate(current, results, context))

                trace.append(
                    ValidationTraceEvent(
                        event="safety_gate",
                        iteration=iteration,
                        payload={"passed": gate_passed},
                    )
                )

                return ValidationResult(
                    decision=(
                        ValidationDecision.RELEASE
                        if gate_passed
                        else ValidationDecision.BLOCK
                    ),
                    artifact=current,
                    checks=results,
                    failed_checks=[],
                    repair_attempts=repair_attempts,
                    iterations=iteration,
                    trace=trace,
                )

            can_repair = (
                self.repair is not None
                and repair_attempts < self.max_repair_iterations
                and all(result.repairable for result in failed)
            )

            if not can_repair:
                return ValidationResult(
                    decision=ValidationDecision.BLOCK,
                    artifact=current,
                    checks=results,
                    failed_checks=failed,
                    repair_attempts=repair_attempts,
                    iterations=iteration,
                    trace=trace,
                )

            repair_attempts += 1
            current = self.repair(current, failed, context)

            trace.append(
                ValidationTraceEvent(
                    event="repair",
                    iteration=iteration,
                    payload={
                        "attempt": repair_attempts,
                        "failed_check_ids": [r.check_id for r in failed],
                    },
                )
            )
