"""HTTP-клиент к core-сервису (backend API).

Бот выступает сервисом: ходит в core с сервисным JWT (``type=service``),
подписанным ``CORE_SERVICE_SECRET`` (тем же, что ``SERVICE_JWT_SECRET`` в core).

Ручки (см. README, раздел «Требования к core»):
- POST /api/v0.0.1/users/link — привязать провайдера к пользователю.
- GET  /api/v0.0.1/users/link?provider=&external_id= — найти связку.
  ЭТОЙ РУЧКИ В CORE ПОКА НЕТ — её нужно добавить (спека в README).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any

import aiohttp

from config.core_config import settings_core
from utils.logging import get_logger

logger = get_logger(__name__)


class CoreError(Exception):
    """Ошибка обращения к core."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class CoreNotFound(CoreError):
    """Связка не найдена (404)."""


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _build_service_token() -> str:
    header = {"alg": settings_core.CORE_SERVICE_ALG, "typ": "JWT"}
    payload = {"type": "service"}
    signing_input = ".".join(
        (
            _b64url_encode(json.dumps(header, separators=(",", ":")).encode()),
            _b64url_encode(json.dumps(
                payload, separators=(",", ":")).encode()),
        )
    )
    signature = hmac.new(
        settings_core.CORE_SERVICE_SECRET.encode(),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


class CoreClient:
    """Тонкий клиент core API."""

    def __init__(self) -> None:
        self._base_url = settings_core.CORE_BASE_URL.rstrip("/")
        self._timeout = settings_core.CORE_TIMEOUT_SEC
        self._service_token = _build_service_token()

    @property
    def _provider(self) -> str:
        return settings_core.CORE_PROVIDER

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        bearer: str | None = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        token = bearer or self._service_token
        headers = {"Authorization": f"Bearer {token}"}
        timeout = aiohttp.ClientTimeout(total=self._timeout)

        logger.debug("Core request: %s %s params=%s", method, url, params)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.request(
                method, url, json=json_body, params=params, headers=headers
            ) as resp:
                body_text = await resp.text()
                if resp.status >= 400:
                    logger.warning(
                        "Core response error: %s %s -> %s (%s)",
                        method, url, resp.status, body_text[:300],
                    )
                    if resp.status == 404:
                        raise CoreNotFound(
                            f"NotFound: {method} {path}", status=404)
                    raise CoreError(
                        f"{method} {path} failed: {resp.status}",
                        status=resp.status,
                    )
                if not body_text:
                    return None
                try:
                    return json.loads(body_text)
                except json.JSONDecodeError:
                    logger.error("Core returned non-JSON: %s", body_text[:300])
                    return None

    async def create_link(
        self,
        *,
        user_id: int,
        external_id: str,
        service_token: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """POST /users/link — привязать внешнего пользователя к core-пользователю.

        ``service_token`` (если передан в deep-link) используется как Bearer,
        иначе — сервисный токен.
        """
        return await self._request(
            "POST",
            settings_core.CORE_LINK_PATH,
            json_body={
                "user_id": user_id,
                "provider": self._provider,
                "external_id": external_id,
                "options": options or {},
            },
            bearer=service_token,
        )

    async def get_link(self, external_id: str) -> dict[str, Any] | None:
        """GET /users/link — найти связку по provider + external_id.

        Возвращает dict со связкой или None, если связки нет.
        """
        try:
            return await self._request(
                "GET",
                settings_core.CORE_LINK_PATH,
                params={
                    "provider": self._provider,
                    "external_id": external_id,
                },
            )
        except CoreNotFound:
            return None
