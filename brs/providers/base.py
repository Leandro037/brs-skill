from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderResponse:
    text: str
    model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class TextProvider(Protocol):
    def generate(self, *, instructions: str, input_text: str) -> ProviderResponse:
        ...
