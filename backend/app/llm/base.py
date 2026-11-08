from typing import Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    """The model call failed or returned output that never validated."""


class LLMProvider(Protocol):
    """Provider-neutral interface; routes depend on this, never on a vendor SDK."""

    def generate_structured(self, system: str, prompt: str, schema: type[T]) -> T:
        """Return `schema`-validated JSON. Retries once, then raises LLMError."""
        ...
