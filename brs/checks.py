from __future__ import annotations

from typing import Any, Callable, Protocol

from .models import CheckResult


class Check(Protocol):
    def __call__(self, artifact: Any, context: dict[str, Any]) -> CheckResult:
        ...


RepairFn = Callable[[Any, list[CheckResult], dict[str, Any]], Any]
SafetyGateFn = Callable[[Any, list[CheckResult], dict[str, Any]], bool]
