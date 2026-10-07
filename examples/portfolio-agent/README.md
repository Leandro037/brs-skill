# E15 · BRS Portfolio Agent

A real-world demonstration of BRS applied to an editable professional landing page.

## What it demonstrates

The site is a working portfolio landing with:

- tech-style navigation and microinteractions;
- horizontal project carousel;
- editable copy stored in localStorage;
- optional AI editing;
- BRS validation before AI-generated content is applied;
- RELEASE / BLOCK feedback in the UI.

## Run locally

From the repository root:

```bash
python -m pip install -e ".[openai]"
python -m apps.portfolio_agent
```

Then open:

```text
http://127.0.0.1:8015
```

The page works without OpenAI for normal browsing and manual editing.

For AI editing, configure:

```text
OPENAI_API_KEY
```

Optionally:

```text
BRS_PORTFOLIO_MODEL=gpt-4o-mini
```

## E15 flow

```text
User edit request
      ↓
AI proposes complete portfolio JSON
      ↓
BRS validates structure + semantic constraints
      ↓
FAIL → localized AI repair
      ↓
full BRS revalidation
      ↓
RELEASE / BLOCK
      ↓
landing updates only on RELEASE
```

## Boundaries

This demo validates the portfolio content contract. It does not claim that the generated copy is factually verified against external sources. Public facts should be supplied as immutable context or checked by an external oracle in stronger experiments.
