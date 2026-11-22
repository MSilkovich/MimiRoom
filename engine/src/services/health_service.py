"""Healthcheck engine: фоновые реальные проверки + дешёвый endpoint.

Монитор раз в ``HEALTHCHECK_INTERVAL_SEC`` проверяет Redis, core (backend) и,
опционально, LLM. Результат держим в памяти; ``/healthcheck`` только читает
снимок и не открывает соединений на каждый запрос.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

import httpx

from config.backend import settings_backend
from config.health import settings_health
from config.llm import settings_llm
from config.project_config import settings_app
from src.logging import get_logger
from src.services.redis_connection import get_redis

logger = get_logger(__name__)

_checks: dict[str, dict[str, Any]] = {}
_task: asyncio.Task | None = None
_http_backend: httpx.AsyncClient | None = None
_started_at = time.monotonic()

CheckFn = Callable[[], Awaitable[None]]


async def _check_redis() -> None:
    r = await get_redis()
    await r.ping()


async def _check_backend() -> None:
    if _http_backend is None:
        raise RuntimeError("HTTP client is not initialized")
    resp = await _http_backend.get("/healthcheck")
    if resp.status_code != 200:
        raise RuntimeError(
            f"backend /healthcheck -> {resp.status_code}: {resp.text[:200]}"
        )


async def _check_llm() -> None:
    timeout = settings_health.HEALTHCHECK_TIMEOUT_SEC
    url = f"{settings_llm.LLM_BASE_URL.rstrip('/')}/models"
    headers = {"Authorization": f"Bearer {settings_llm.LLM_API_KEY}"}
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, headers=headers)
    if resp.status_code >= 400:
        raise RuntimeError(f"LLM /models -> {resp.status_code}")


def _build_checks() -> list[tuple[str, CheckFn, bool]]:
    checks: list[tuple[str, CheckFn, bool]] = [("redis", _check_redis, True)]
    if settings_health.HEALTHCHECK_BACKEND_ENABLED:
        checks.append(("backend", _check_backend, True))
    if settings_health.HEALTHCHECK_LLM_ENABLED:
        checks.append(("llm", _check_llm, False))
    return checks


async def _run_check(name: str, fn: CheckFn, required: bool) -> dict[str, Any]:
    started = time.perf_counter()
    checked_at = datetime.now(timezone.utc)
    status = "ok"
    error: str | None = None

    try:
        await asyncio.wait_for(fn(), timeout=settings_health.HEALTHCHECK_TIMEOUT_SEC)
    except asyncio.CancelledError:
        raise
    except Exception as exc:  # noqa: BLE001
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
    checks = _build_checks()
    results = await asyncio.gather(
        *(_run_check(name, fn, required) for name, fn, required in checks)
    )
    for (name, _fn, _required), result in zip(checks, results):
        _checks[name] = result


def get_health_snapshot() -> dict[str, Any]:
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
    global _task, _http_backend
    _http_backend = httpx.AsyncClient(
        base_url=settings_backend.BACKEND_BASE_URL.rstrip("/"),
        timeout=settings_health.HEALTHCHECK_TIMEOUT_SEC,
    )
    await refresh_health()
    _task = asyncio.create_task(_monitor_loop(), name="health-monitor")


async def stop_health_monitor() -> None:
    global _task, _http_backend
    if _task is not None:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None
    if _http_backend is not None:
        await _http_backend.aclose()
        _http_backend = None
