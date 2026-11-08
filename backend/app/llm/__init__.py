from app.core.config import get_settings
from app.llm.base import LLMError, LLMProvider


def get_llm() -> LLMProvider:
    """FastAPI dependency; tests override it. Swap providers here only."""
    from app.llm.gemini import GeminiProvider

    return GeminiProvider(get_settings())


__all__ = ["LLMError", "LLMProvider", "get_llm"]
