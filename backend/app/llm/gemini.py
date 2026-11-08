from google import genai
from google.genai import types
from pydantic import ValidationError

from app.core.config import Settings
from app.llm.base import LLMError, T


class GeminiProvider:
    def __init__(self, settings: Settings) -> None:
        if not settings.gemini_api_key or not settings.llm_model:
            raise LLMError("LLM is not configured (GEMINI_API_KEY / LLM_MODEL)")
        self._client = genai.Client(api_key=settings.gemini_api_key)
        self._model = settings.llm_model

    def _call(self, system: str, prompt: str, schema: type[T]) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.2,
            ),
        )
        return response.text or ""

    def generate_structured(self, system: str, prompt: str, schema: type[T]) -> T:
        last_error: Exception | None = None
        for _attempt in range(2):  # hard rule 4: retry once, then fail cleanly
            try:
                return schema.model_validate_json(self._call(system, prompt, schema))
            except (ValidationError, ValueError) as exc:
                last_error = exc
            except Exception as exc:  # SDK/network errors
                raise LLMError("The AI service is unavailable") from exc
        raise LLMError("The AI service returned an invalid response") from last_error
