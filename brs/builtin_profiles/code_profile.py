from __future__ import annotations

import ast
from typing import Any

from brs.models import CheckResult, CheckStatus
from brs.profiles import BRSProfile


def make_code_profile(*, language: str = "python") -> BRSProfile:
    """Create a conservative static code-validation profile.

    v0.2 supports Python syntax validation. It does not execute untrusted code.
    """

    if language.lower() != "python":
        raise ValueError("BRS v0.2 code profile currently supports only Python")

    def is_text(artifact: Any, context: dict[str, Any]) -> CheckResult:
        ok = isinstance(artifact, str) and bool(artifact.strip())
        return CheckResult(
            check_id="CODE_NONEMPTY_TEXT",
            status=CheckStatus.PASS if ok else CheckStatus.FAIL,
            evidence="non-empty source text" if ok else "artifact must be non-empty source text",
            repairable=False,
        )

    def parses(artifact: Any, context: dict[str, Any]) -> CheckResult:
        if not isinstance(artifact, str):
            return CheckResult(
                check_id="CODE_PYTHON_SYNTAX",
                status=CheckStatus.FAIL,
                evidence="cannot parse non-string artifact",
                repairable=False,
            )
        try:
            ast.parse(artifact)
            return CheckResult(
                check_id="CODE_PYTHON_SYNTAX",
                status=CheckStatus.PASS,
                evidence="Python AST parse succeeded",
            )
        except SyntaxError as exc:
            return CheckResult(
                check_id="CODE_PYTHON_SYNTAX",
                status=CheckStatus.FAIL,
                evidence=f"syntax error at line {exc.lineno}: {exc.msg}",
                repairable=False,
                metadata={"line": exc.lineno, "message": exc.msg},
            )

    def no_obvious_placeholders(artifact: Any, context: dict[str, Any]) -> CheckResult:
        if not isinstance(artifact, str):
            return CheckResult(
                check_id="CODE_NO_PLACEHOLDERS",
                status=CheckStatus.FAIL,
                evidence="cannot inspect non-string artifact",
                repairable=False,
            )
        markers = ("TODO", "FIXME", "pass  # TODO", "<YOUR_", "INSERT_HERE")
        found = [marker for marker in markers if marker in artifact]
        return CheckResult(
            check_id="CODE_NO_PLACEHOLDERS",
            status=CheckStatus.PASS if not found else CheckStatus.FAIL,
            evidence="no configured placeholder markers found" if not found else f"placeholder markers: {found}",
            repairable=False,
            metadata={"markers": found},
        )

    return BRSProfile(
        name="code-python",
        checks=[is_text, parses, no_obvious_placeholders],
    )
