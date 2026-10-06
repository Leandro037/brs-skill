from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .checks import Check, RepairFn, SafetyGateFn


@dataclass
class BRSProfile:
    name: str
    checks: list[Check] = field(default_factory=list)
    repair: RepairFn | None = None
    safety_gate: SafetyGateFn | None = None
    context_defaults: dict[str, Any] = field(default_factory=dict)
