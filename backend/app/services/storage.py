from typing import Protocol

import httpx

from app.core.config import get_settings

BUCKET = "cvs"
MAX_SIGNED_URL_SECONDS = 600  # hard rule 5: signed URLs live at most 10 minutes


class StorageError(RuntimeError):
    pass


class CvStorage(Protocol):
    def upload(self, path: str, data: bytes, content_type: str) -> None: ...
    def delete(self, path: str) -> None: ...
    def signed_url(self, path: str) -> str: ...


class SupabaseStorage:
    """Talks to the private `cvs` bucket with the service key (backend only)."""

    def __init__(self) -> None:
        s = get_settings()
        if not s.supabase_url or not s.supabase_service_key:
            raise StorageError("Storage is not configured")
        self._base = f"{s.supabase_url.rstrip('/')}/storage/v1"
        self._headers = {
            "Authorization": f"Bearer {s.supabase_service_key}",
            "apikey": s.supabase_service_key,
        }

    def _request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
        try:
            response = httpx.request(method, url, headers=self._headers, timeout=30, **kwargs)  # type: ignore[arg-type]
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise StorageError("Storage request failed") from exc
        return response

    def upload(self, path: str, data: bytes, content_type: str) -> None:
        self._request(
            "POST",
            f"{self._base}/object/{BUCKET}/{path}",
            content=data,
            headers={**self._headers, "Content-Type": content_type},
        )

    def delete(self, path: str) -> None:
        self._request("DELETE", f"{self._base}/object/{BUCKET}/{path}")

    def signed_url(self, path: str) -> str:
        response = self._request(
            "POST",
            f"{self._base}/object/sign/{BUCKET}/{path}",
            json={"expiresIn": MAX_SIGNED_URL_SECONDS},
        )
        return f"{self._base}{response.json()['signedURL']}"


def get_storage() -> CvStorage:
    """FastAPI dependency; tests override it."""
    return SupabaseStorage()
