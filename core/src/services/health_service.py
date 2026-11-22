"""Реальные healthcheck-проверки без похода в БД/Redis на каждый HTTP-запрос.

Идея: фоновый монитор раз в ``HEALTHCHECK_INTERVAL_SEC`` проверяет зависимости
(БД, Redis) и складывает результат в память. ``/healthcheck`` просто отдаёт
последний снимок — O(1), без открытия соединений.

Это компромисс: проверки реальные, но дорогие операции не привязаны к частоте
healthcheck-запросов (Docker может дергать /healthcheck каждые 2 секунды).
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from sqlalchemy import text

from config.database.db_helper import db_helper
from config.health import settings_health
from config.project_config import settings_app
from src.apps.core.logging import get_logger
from src.services.link_code_service import get_redis

logger = get_logger(__name__)

_checks: dict[str, dict[str, Any]] = {}
_task: asyncio.Task | None = None
_started_at = time.monotonic()

CheckFn = Callable[[], Awaitable[None]]


async def _check_database() -> None:
    async with db_helper.engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def _check_redis() -> None:
    r = await get_redis()
    await r.ping()


# (имя, функция, обязательная ли проверка)
_CHECKS: list[tuple[str, CheckFn, bool]] = [
    ("database", _check_database, True),
    ("redis", _check_redis, True),
]


async def _run_check(name: str, fn: CheckFn, required: bool) -> dict[str, Any]:
    started = time.perf_counter()
    checked_at = datetime.now(timezone.utc)
    status = "ok"
    error: str | None = None

    try:
        await asyncio.wait_for(fn(), timeout=settings_health.HEALTHCHECK_TIMEOUT_SEC)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001 — любая ошибка зависимости
        status = "error"
        error = f"{type(exc).__name__}: {exc}"
        logger.warning("Healthcheck '%s' failed: %s", name, error)

    return {
        "status": status,
        "required": required,
        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        "checked_at": checked_at.isoformat(),
        "error": error,
    }


async def refresh_health() -> None:
    """Выполнить все проверки и обновить снимок."""
    results = await asyncio.gather(
        *(_run_check(name, fn, required) for name, fn, required in _CHECKS)
    )
    for (name, _fn, _required), result in zip(_CHECKS, results):
        _checks[name] = result


def get_health_snapshot() -> dict[str, Any]:
    """Отдать последний снимок healthcheck (без сетевых операций)."""
    required_error = any(
        c["status"] == "error" and c["required"] for c in _checks.values()
    )
    optional_error = any(
        c["status"] == "error" and not c["required"] for c in _checks.values()
    )

    if not _checks:
        overall = "starting"
    elif required_error:
        overall = "error"
    elif optional_error:
        overall = "degraded"
    else:
        overall = "ok"

    return {
        "status": overall,
        "project": settings_app.PROJECT_NAME,
        "version": settings_app.VERSION,
        "uptime_sec": round(time.monotonic() - _started_at, 2),
        "checks": _checks,
    }


async def _monitor_loop() -> None:
    while True:
        await asyncio.sleep(settings_health.HEALTHCHECK_INTERVAL_SEC)
        try:
            await refresh_health()
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception("Healthcheck cycle failed")


async def start_health_monitor() -> None:
    """Первичная проверка + фоновый цикл."""
    global _task
    await refresh_health()
    _task = asyncio.create_task(_monitor_loop(), name="health-monitor")


async def stop_health_monitor() -> None:
    global _task
    if _task is not None:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None
