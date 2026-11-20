"""Базовый HTTP-клиент для запросов к backend API.

Репозитории наследуются от BaseRepository и используют _request()
для GET/POST/PUT/DELETE запросов.
"""

from typing import Any

import httpx

from config.backend import settings_backend
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
        params: dict[str, Any] | None = None
    ) -> Any:
        """Выполнить HTTP-запрос к backend API и вернуть JSON-ответ."""
        url = f"{self._base_url}{path}"
        logger.debug(
            "Backend request: %s %s params=%s",
            method, url, params,
        )
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.request(
                method,
                url,
                json=json,
                params=params,
                headers={"Authorization": f"Bearer {self._token}"},
            )
            # resp.raise_for_status()
            body: Any = resp.json()
            logger.debug(
                "Backend response: %s %s with token %s -> %s",
                method, url, self._token, resp.status_code,
            )
            return body
