from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class ValidationDecision(str, Enum):
    RELEASE = "RELEASE"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    status: CheckStatus
    evidence: str = ""
    mandatory: bool = True
    repairable: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ValidationTraceEvent:
    event: str
    iteration: int
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    decision: ValidationDecision
    artifact: Any
    checks: list[CheckResult]
    failed_checks: list[CheckResult]
    repair_attempts: int
    iterations: int
    trace: list[ValidationTraceEvent]
