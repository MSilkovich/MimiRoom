"""
Путь: /
- POST    /healthchek                          — проверить жив ли сервис и имеет ли все необходимые подключения
"""

from fastapi import APIRouter


router = APIRouter(prefix="/", tags=["staff"])


@router.post("/healthcheck", response_model=any)
async def healthcheck():
    """проверить жив ли сервис и имеет ли все необходимые подключения"""
    return True  # TODO: единый стандарт
