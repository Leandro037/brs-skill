from __future__ import annotations

from typing import Any

from .engine import BRS
from .profiles import BRSProfile


def brs_from_profile(
    profile: BRSProfile,
    *,
    max_repair_iterations: int = 1,
    context: dict[str, Any] | None = None,
) -> tuple[BRS, dict[str, Any]]:
    """Build a BRS engine and merged default context from a profile."""

    merged_context = dict(profile.context_defaults)
    merged_context.update(context or {})

    engine = BRS(
        checks=profile.checks,
        repair=profile.repair,
        safety_gate=profile.safety_gate,
        max_repair_iterations=max_repair_iterations,
    )
    return engine, merged_context
