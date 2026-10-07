import json
from pathlib import Path

from apps.portfolio_agent import ai_edit_portfolio, validate_portfolio
from brs.providers.base import ProviderResponse


ROOT = Path(__file__).resolve().parents[1]
PORTFOLIO = json.loads(
    (ROOT / "examples" / "portfolio-agent" / "site" / "portfolio.json").read_text(encoding="utf-8")
)


class FakeProvider:
    def __init__(self, outputs):
        self.outputs = list(outputs)

    def generate(self, *, instructions, input_text):
        return ProviderResponse(
            text=self.outputs.pop(0),
            model="fake",
            input_tokens=10,
            output_tokens=10,
            total_tokens=20,
        )


def test_seed_portfolio_releases():
    result = validate_portfolio(PORTFOLIO)
    assert result.decision.value == "RELEASE"


def test_missing_projects_blocks():
    broken = dict(PORTFOLIO)
    broken.pop("projects")
    result = validate_portfolio(broken)
    assert result.decision.value == "BLOCK"
    assert "PORTFOLIO_REQUIRED_SECTIONS" in [x.check_id for x in result.failed_checks]


def test_invalid_contact_url_blocks():
    broken = json.loads(json.dumps(PORTFOLIO))
    broken["contact"]["links"][0]["url"] = "javascript:alert(1)"
    result = validate_portfolio(broken)
    assert result.decision.value == "BLOCK"
    failed = [x.check_id for x in result.failed_checks]
    assert "PORTFOLIO_CONTACT" in failed or "PORTFOLIO_URLS" in failed


def test_ai_edit_valid_release():
    updated = json.loads(json.dumps(PORTFOLIO))
    updated["hero"]["title"] = "Nueva propuesta profesional"
    provider = FakeProvider([json.dumps(updated)])

    result = ai_edit_portfolio(
        prompt="Actualiza el hero",
        portfolio=PORTFOLIO,
        provider=provider,
    )

    assert result["decision"] == "RELEASE"
    assert result["artifact"]["hero"]["title"] == "Nueva propuesta profesional"
    assert result["repair_attempts"] == 0


def test_ai_edit_repairs_invalid_candidate_then_releases():
    broken = json.loads(json.dumps(PORTFOLIO))
    broken.pop("skills")
    repaired = json.loads(json.dumps(PORTFOLIO))
    repaired["hero"]["title"] = "Hero reparado"

    provider = FakeProvider([
        json.dumps(broken),
        json.dumps(repaired),
    ])

    result = ai_edit_portfolio(
        prompt="Cambia el hero",
        portfolio=PORTFOLIO,
        provider=provider,
    )

    assert result["decision"] == "RELEASE"
    assert result["repair_attempts"] == 1
    assert result["iterations"] == 2
    assert result["artifact"]["hero"]["title"] == "Hero reparado"
