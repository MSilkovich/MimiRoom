"""
Путь: /healthcheck
- POST   /healthcheck                     — проверить жив ли сервис
"""

from fastapi import APIRouter


router = APIRouter(prefix="", tags=["staff"], include_in_schema=False)


@router.post("/healthcheck")
async def healthcheck():
    """Проверить жив ли сервис и имеет ли все необходимые подключения."""
    return {"status": "ok"}  # TODO: полноценная проверка (Redis, LLM, backend)
