from __future__ import annotations

import re
from typing import Any

from brs.models import CheckResult, CheckStatus
from brs.profiles import BRSProfile


def make_research_document_profile(
    *,
    required_sections: tuple[str, ...] = ("Abstract", "Method", "Results", "Limitations"),
    require_references: bool = True,
) -> BRSProfile:
    """Create a structural profile for Markdown research documents.

    The profile checks structure only. It does not establish scientific truth,
    citation validity, statistical correctness, or publication readiness.
    """

    def is_text(artifact: Any, context: dict[str, Any]) -> CheckResult:
        ok = isinstance(artifact, str) and bool(artifact.strip())
        return CheckResult(
            check_id="DOC_NONEMPTY_TEXT",
            status=CheckStatus.PASS if ok else CheckStatus.FAIL,
            evidence="document contains text" if ok else "document is empty or not text",
            repairable=False,
        )

    def required_headings(artifact: Any, context: dict[str, Any]) -> CheckResult:
        if not isinstance(artifact, str):
            return CheckResult(
                check_id="DOC_REQUIRED_SECTIONS",
                status=CheckStatus.FAIL,
                evidence="cannot inspect headings in non-text artifact",
                repairable=False,
            )
        headings = {
            match.group(1).strip().lower()
            for match in re.finditer(r"^#{1,6}\s+(.+?)\s*$", artifact, flags=re.MULTILINE)
        }
        missing = [name for name in required_sections if name.lower() not in headings]
        return CheckResult(
            check_id="DOC_REQUIRED_SECTIONS",
            status=CheckStatus.PASS if not missing else CheckStatus.FAIL,
            evidence="required sections present" if not missing else f"missing sections: {missing}",
            repairable=False,
            metadata={"missing": missing},
        )

    def references_present(artifact: Any, context: dict[str, Any]) -> CheckResult:
        if not require_references:
            return CheckResult(
                check_id="DOC_REFERENCES_SECTION",
                status=CheckStatus.PASS,
                evidence="reference-section requirement disabled",
                mandatory=False,
            )
        if not isinstance(artifact, str):
            return CheckResult(
                check_id="DOC_REFERENCES_SECTION",
                status=CheckStatus.FAIL,
                evidence="cannot inspect references in non-text artifact",
                repairable=False,
            )
        ok = bool(re.search(r"^#{1,6}\s+(References|Bibliography)\s*$", artifact, flags=re.MULTILINE | re.IGNORECASE))
        return CheckResult(
            check_id="DOC_REFERENCES_SECTION",
            status=CheckStatus.PASS if ok else CheckStatus.FAIL,
            evidence="references section present" if ok else "missing References/Bibliography heading",
            repairable=False,
        )

    def limitations_are_explicit(artifact: Any, context: dict[str, Any]) -> CheckResult:
        if not isinstance(artifact, str):
            return CheckResult(
                check_id="DOC_LIMITATIONS_EXPLICIT",
                status=CheckStatus.FAIL,
                evidence="cannot inspect limitations in non-text artifact",
                repairable=False,
            )
        ok = bool(re.search(r"^#{1,6}\s+(Limitations|Threats to Validity)\s*$", artifact, flags=re.MULTILINE | re.IGNORECASE))
        return CheckResult(
            check_id="DOC_LIMITATIONS_EXPLICIT",
            status=CheckStatus.PASS if ok else CheckStatus.FAIL,
            evidence="limitations are explicitly sectioned" if ok else "no explicit Limitations/Threats to Validity section",
            repairable=False,
        )

    return BRSProfile(
        name="research-document",
        checks=[is_text, required_headings, references_present, limitations_are_explicit],
    )
