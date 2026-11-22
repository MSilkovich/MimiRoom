"""Базовый HTTP-клиент для запросов к backend API.

Репозитории наследуются от BaseRepository и используют _request()
для GET/POST/PUT/DELETE запросов.
"""

from typing import Any

import httpx

from config.backend import settings_backend
from src.exceptions import BackendError, BackendNotFoundError
from src.logging import get_logger

logger = get_logger(__name__)


class BaseRepository:
    """Базовый класс для репозиториев backend API."""

    def __init__(self) -> None:
        self._base_url = settings_backend.BACKEND_BASE_URL.rstrip("/")
        self._token = settings_backend.token
        self._timeout = settings_backend.BACKEND_TIMEOUT_SEC

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Выполнить HTTP-запрос к backend API и вернуть JSON-ответ.

        Raises:
            BackendNotFoundError: backend вернул 404.
            BackendError: сетевая ошибка, 4xx/5xx или невалидный JSON.
        """
        url = f"{self._base_url}{path}"
        logger.debug(
            "Backend request: %s %s params=%s", method, url, params
        )

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.request(
                    method,
                    url,
                    json=json,
                    params=params,
                    headers={"Authorization": f"Bearer {self._token}"},
                )
        except httpx.HTTPError as exc:
            raise BackendError(
                f"Backend request failed: {method} {path}: {exc}"
            ) from exc

        if resp.status_code == 404:
            raise BackendNotFoundError(f"Backend 404: {method} {path}")

        if resp.status_code >= 400:
            raise BackendError(
                f"Backend error: {method} {path} -> {resp.status_code}: "
                f"{resp.text[:300]}"
            )

        logger.debug(
            "Backend response: %s %s -> %s", method, url, resp.status_code
        )

        if not resp.content:
            return None

        try:
            return resp.json()
        except ValueError as exc:
            raise BackendError(
                f"Backend returned invalid JSON: {method} {path}"
            ) from exc
