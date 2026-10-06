# OpenAI Adapter

BRS Skill v0.3 adds an optional OpenAI adapter using the Responses API.

The BRS core remains provider-agnostic. OpenAI is used only for generation and, when explicitly enabled, localized repair.

## Install

```bash
python -m pip install -e ".[openai]"
```

## Configure

Set your API key as an environment variable. Do not commit it to Git.

### macOS / Linux

```bash
export OPENAI_API_KEY="..."
```

### PowerShell

```powershell
$env:OPENAI_API_KEY="..."
```

Optional model override:

```powershell
$env:BRS_OPENAI_MODEL="gpt-6-luna"
```

The default model in v0.3 is `gpt-6-luna`, chosen as a low-cost general model. You can override it without changing the code.

## Run the example

```bash
python examples/openai_end_to_end.py
```

The flow is:

```text
Prompt
  ↓
OpenAI generation
  ↓
BRS validation
  ↓
FAIL ─→ localized OpenAI repair
             ↓
        full revalidation
             ↓
        RELEASE / BLOCK
```

## Safety behavior

- generation output that cannot be parsed by the selected codec is blocked;
- repair is opt-in by check ID;
- repair output that cannot be parsed fails closed;
- every repair is followed by complete BRS revalidation;
- BRS, not the model, makes the final release decision;
- the adapter records token counts when the provider returns usage metadata.

## What this does not prove

A working OpenAI adapter does not demonstrate that BRS improves reliability across models or domains. That requires controlled comparison such as:

- generation without BRS;
- generation with BRS;
- defect escape rate;
- repair success;
- latency;
- token usage;
- API cost;
- multiple models and domains.

The adapter is infrastructure for that future evaluation.
