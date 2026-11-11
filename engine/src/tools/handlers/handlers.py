"""Handlers инструментов: тонкие HTTP-клиенты к вашему REST API."""

from src.logging import get_logger
from typing import Any

import httpx

from config.backend import settings_backend

logger = get_logger(__name__)


async def _call_backend(
    method: str, path: str, *, json: dict | None = None
) -> dict[str, Any]:
    async with httpx.AsyncClient(
        base_url=settings_backend.BACKEND_URL,
        timeout=settings_backend.BACKEND_TIMEOUT_SEC,
    ) as client:
        resp = await client.request(
            method,
            path,
            json=json,
            headers={"X-Service-Token": settings_backend.BACKEND_SERVICE_TOKEN},
        )
        resp.raise_for_status()
        return resp.json()


async def get_services(user_id: int, **_: Any) -> dict[str, Any]:
    return await _call_backend("GET", "/api/services")
