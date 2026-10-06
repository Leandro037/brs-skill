from __future__ import annotations

import os
from typing import Any

from .base import ProviderResponse


class OpenAIResponsesProvider:
    """OpenAI Responses API adapter.

    The OpenAI SDK is imported lazily so BRS Core remains provider-agnostic.
    A client can be injected for tests, which avoids network calls and secrets.
    """

    def __init__(
        self,
        *,
        model: str | None = None,
        client: Any | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model = model or os.getenv("BRS_OPENAI_MODEL", "gpt-6-luna")

        if client is not None:
            self.client = client
            return

        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "OpenAI integration requires the optional dependency. "
                "Install with: python -m pip install -e '.[openai]'"
            ) from exc

        self.client = OpenAI(api_key=api_key) if api_key else OpenAI()

    def generate(self, *, instructions: str, input_text: str) -> ProviderResponse:
        response = self.client.responses.create(
            model=self.model,
            instructions=instructions,
            input=input_text,
        )

        usage = getattr(response, "usage", None)
        return ProviderResponse(
            text=getattr(response, "output_text", "") or "",
            model=getattr(response, "model", self.model),
            input_tokens=getattr(usage, "input_tokens", None) if usage else None,
            output_tokens=getattr(usage, "output_tokens", None) if usage else None,
            total_tokens=getattr(usage, "total_tokens", None) if usage else None,
        )
