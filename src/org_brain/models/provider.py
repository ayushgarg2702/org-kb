"""Provider-neutral model adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass
class ModelUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = "none"


class ModelProvider(Protocol):
    name: str

    def complete(self, prompt: str, *, system: str | None = None) -> tuple[str, ModelUsage]: ...


class NullModelProvider:
    name = "none"

    def complete(self, prompt: str, *, system: str | None = None) -> tuple[str, ModelUsage]:
        return ("", ModelUsage())


class EchoModelProvider:
    """Deterministic stub for tests — does not invent org facts."""

    name = "echo"

    def complete(self, prompt: str, *, system: str | None = None) -> tuple[str, ModelUsage]:
        text = "Based on the provided evidence only:\n" + prompt[:2000]
        return text, ModelUsage(
            input_tokens=len(prompt.split()), output_tokens=len(text.split()), model="echo"
        )


def get_provider(name: str | None) -> ModelProvider:
    if not name or name in {"none", "configured-provider"}:
        return NullModelProvider()
    if name == "echo":
        return EchoModelProvider()
    # Unknown providers fall back to null rather than inventing network calls.
    return NullModelProvider()
