"""Служебный роутер: healthcheck."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.services.health_service import get_health_snapshot

router = APIRouter(prefix="", tags=["staff"], include_in_schema=False)


@router.get("/healthcheck")
async def healthcheck():
    """Проверить сервис и зависимости (Redis, core, опционально LLM).

    Отдаёт последний снимок фонового монитора; ``200`` — ok/degraded,
    ``503`` — error/starting.
    """
    snapshot = get_health_snapshot()
    status_code = 200 if snapshot["status"] in ("ok", "degraded") else 503
    return JSONResponse(status_code=status_code, content=snapshot)
