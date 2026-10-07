from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from brs.agentic import JSON_CODEC, with_provider_repair
from brs.factory import brs_from_profile
from brs.models import CheckResult, CheckStatus
from brs.profiles import BRSProfile
from brs.providers import OpenAIResponsesProvider

ROOT = Path(__file__).resolve().parents[1]
SITE_DIR = ROOT / "examples" / "portfolio-agent" / "site"

REQUIRED_TOP_LEVEL = {
    "hero", "stats", "about", "projects", "experience", "skills", "contact"
}

REPAIRABLE_CHECKS = {
    "PORTFOLIO_ROOT",
    "PORTFOLIO_REQUIRED_SECTIONS",
    "PORTFOLIO_HERO",
    "PORTFOLIO_STATS",
    "PORTFOLIO_PROJECTS",
    "PORTFOLIO_EXPERIENCE",
    "PORTFOLIO_SKILLS",
    "PORTFOLIO_CONTACT",
    "PORTFOLIO_URLS",
}


def _pass(check_id: str, evidence: str) -> CheckResult:
    return CheckResult(check_id, CheckStatus.PASS, evidence, mandatory=True, repairable=True)


def _fail(check_id: str, evidence: str) -> CheckResult:
    return CheckResult(check_id, CheckStatus.FAIL, evidence, mandatory=True, repairable=True)


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _url_ok(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if value.startswith("#"):
        return len(value) > 1
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def make_portfolio_profile() -> BRSProfile:
    def root_check(artifact, context):
        return (
            _pass("PORTFOLIO_ROOT", "portfolio is a JSON object")
            if isinstance(artifact, dict)
            else _fail("PORTFOLIO_ROOT", f"expected object, got {type(artifact).__name__}")
        )

    def sections_check(artifact, context):
        if not isinstance(artifact, dict):
            return _fail("PORTFOLIO_REQUIRED_SECTIONS", "cannot inspect sections on non-object")
        missing = sorted(REQUIRED_TOP_LEVEL - set(artifact))
        return (
            _pass("PORTFOLIO_REQUIRED_SECTIONS", "all required sections present")
            if not missing
            else _fail("PORTFOLIO_REQUIRED_SECTIONS", f"missing sections: {', '.join(missing)}")
        )

    def hero_check(artifact, context):
        hero = artifact.get("hero") if isinstance(artifact, dict) else None
        keys = ("eyebrow", "title", "subtitle", "primaryCta", "secondaryCta")
        bad = [key for key in keys if not isinstance(hero, dict) or not _non_empty_text(hero.get(key))]
        return _pass("PORTFOLIO_HERO", "hero contract valid") if not bad else _fail(
            "PORTFOLIO_HERO", f"hero missing/empty fields: {', '.join(bad)}"
        )

    def stats_check(artifact, context):
        stats = artifact.get("stats") if isinstance(artifact, dict) else None
        ok = (
            isinstance(stats, list)
            and len(stats) >= 3
            and all(isinstance(x, dict) and _non_empty_text(x.get("value")) and _non_empty_text(x.get("label")) for x in stats)
        )
        return _pass("PORTFOLIO_STATS", f"{len(stats)} stats valid") if ok else _fail(
            "PORTFOLIO_STATS", "stats must contain at least 3 value/label objects"
        )

    def projects_check(artifact, context):
        projects = artifact.get("projects") if isinstance(artifact, dict) else None
        required = ("tag", "title", "description", "metric", "metricLabel", "link")
        ok = (
            isinstance(projects, list)
            and len(projects) >= 3
            and all(
                isinstance(p, dict)
                and all(_non_empty_text(p.get(k)) for k in required)
                for p in projects
            )
        )
        return _pass("PORTFOLIO_PROJECTS", f"{len(projects)} project cards valid") if ok else _fail(
            "PORTFOLIO_PROJECTS", "projects must contain at least 3 complete project cards"
        )

    def experience_check(artifact, context):
        experience = artifact.get("experience") if isinstance(artifact, dict) else None
        required = ("period", "role", "company", "text")
        ok = (
            isinstance(experience, list)
            and len(experience) >= 2
            and all(
                isinstance(item, dict)
                and all(_non_empty_text(item.get(k)) for k in required)
                for item in experience
            )
        )
        return _pass("PORTFOLIO_EXPERIENCE", f"{len(experience)} experience entries valid") if ok else _fail(
            "PORTFOLIO_EXPERIENCE", "experience must contain at least 2 complete entries"
        )

    def skills_check(artifact, context):
        skills = artifact.get("skills") if isinstance(artifact, dict) else None
        ok = isinstance(skills, list) and len(skills) >= 5 and all(_non_empty_text(x) for x in skills)
        return _pass("PORTFOLIO_SKILLS", f"{len(skills)} skills valid") if ok else _fail(
            "PORTFOLIO_SKILLS", "skills must contain at least 5 non-empty strings"
        )

    def contact_check(artifact, context):
        contact = artifact.get("contact") if isinstance(artifact, dict) else None
        ok = (
            isinstance(contact, dict)
            and _non_empty_text(contact.get("title"))
            and _non_empty_text(contact.get("body"))
            and isinstance(contact.get("links"), list)
            and len(contact["links"]) >= 1
            and all(
                isinstance(link, dict)
                and _non_empty_text(link.get("label"))
                and _url_ok(link.get("url"))
                for link in contact["links"]
            )
        )
        return _pass("PORTFOLIO_CONTACT", "contact contract valid") if ok else _fail(
            "PORTFOLIO_CONTACT", "contact requires title, body and valid links"
        )

    def url_check(artifact, context):
        if not isinstance(artifact, dict):
            return _fail("PORTFOLIO_URLS", "cannot inspect URLs on non-object")
        invalid: list[str] = []
        for i, project in enumerate(artifact.get("projects") or []):
            if isinstance(project, dict) and not _url_ok(project.get("link")):
                invalid.append(f"projects[{i}].link")
        contact = artifact.get("contact")
        if isinstance(contact, dict):
            for i, link in enumerate(contact.get("links") or []):
                if isinstance(link, dict) and not _url_ok(link.get("url")):
                    invalid.append(f"contact.links[{i}].url")
        return _pass("PORTFOLIO_URLS", "all links use https/http or local anchors") if not invalid else _fail(
            "PORTFOLIO_URLS", f"invalid URLs: {', '.join(invalid)}"
        )

    return BRSProfile(
        name="portfolio-agent-v1",
        checks=[
            root_check,
            sections_check,
            hero_check,
            stats_check,
            projects_check,
            experience_check,
            skills_check,
            contact_check,
            url_check,
        ],
    )


def validate_portfolio(artifact: Any):
    engine, context = brs_from_profile(make_portfolio_profile(), max_repair_iterations=0)
    return engine.validate(artifact, context=context)


def ai_edit_portfolio(
    *,
    prompt: str,
    portfolio: dict[str, Any],
    provider: Any | None = None,
) -> dict[str, Any]:
    if not prompt.strip():
        return {"decision": "BLOCK", "error": "empty edit prompt"}

    if provider is None:
        provider = OpenAIResponsesProvider(
            model=os.getenv("BRS_PORTFOLIO_MODEL", "gpt-4o-mini")
        )

    generation = provider.generate(
        instructions=(
            "You edit a professional portfolio JSON artifact. "
            "Return only the complete updated JSON object. "
            "Preserve factual claims unless the user explicitly asks to change them. "
            "Do not remove unrelated correct content. "
            "Keep the existing JSON schema and valid links."
        ),
        input_text=(
            "User edit request:\n"
            f"{prompt}\n\n"
            "Current portfolio JSON:\n"
            f"{json.dumps(portfolio, ensure_ascii=False, indent=2)}"
        ),
    )

    try:
        candidate = json.loads(generation.text)
    except Exception as exc:
        return {
            "decision": "BLOCK",
            "error": f"AI output was not valid JSON: {exc}",
            "provider_calls": 1,
        }

    calls = []
    profile = with_provider_repair(
        make_portfolio_profile(),
        provider=provider,
        codec=JSON_CODEC,
        provider_calls=calls,
        allowed_check_ids=REPAIRABLE_CHECKS,
        repair_instructions=(
            "Repair only the listed portfolio validation failures. "
            "Preserve correct content and factual claims. "
            "Return the complete portfolio JSON object and no commentary."
        ),
    )
    engine, context = brs_from_profile(profile, max_repair_iterations=1)
    result = engine.validate(candidate, context=context)

    return {
        "decision": result.decision.value,
        "artifact": result.artifact,
        "checks": [
            {
                "check_id": c.check_id,
                "status": c.status.value,
                "evidence": c.evidence,
            }
            for c in result.checks
        ],
        "failed_checks": [c.check_id for c in result.failed_checks],
        "repair_attempts": result.repair_attempts,
        "iterations": result.iterations,
        "provider_calls": 1 + len(calls),
        "tokens": (generation.total_tokens or 0) + sum(c.total_tokens or 0 for c in calls),
        "summary": (
            "Cambio validado por BRS y listo para aplicar."
            if result.decision.value == "RELEASE"
            else "BRS bloqueó el cambio porque quedaron checks obligatorios en FAIL."
        ),
    }


class PortfolioHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE_DIR), **kwargs)

    def do_POST(self):
        if self.path != "/api/portfolio/edit":
            self.send_error(404)
            return

        try:
            length = min(int(self.headers.get("Content-Length", "0")), 2_000_000)
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            prompt = str(payload.get("prompt", ""))
            portfolio = payload.get("portfolio")
            if not isinstance(portfolio, dict):
                raise ValueError("portfolio must be an object")
            response = ai_edit_portfolio(prompt=prompt, portfolio=portfolio)
            status = 200
        except Exception as exc:
            response = {"decision": "BLOCK", "error": str(exc)}
            status = 400

        body = json.dumps(response, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[portfolio-agent] {fmt % args}")


def main() -> None:
    host = os.getenv("BRS_PORTFOLIO_HOST", "127.0.0.1")
    port = int(os.getenv("BRS_PORTFOLIO_PORT", "8015"))
    server = ThreadingHTTPServer((host, port), PortfolioHandler)
    print(f"BRS Portfolio Agent running at http://{host}:{port}")
    print("Manual editing works without an API key.")
    print("AI editing requires OPENAI_API_KEY.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
