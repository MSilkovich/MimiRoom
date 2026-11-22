"""Привязки внешних провайдеров (UserLink) и одноразовые коды для /start.

Ручки:
- GET    /users/link                       — lookup по provider+external_id
  (access: только своя связка; service: любая).
- GET    /users/link/all                   — список связок текущего пользователя (access).
- POST   /users/link                       — создать/обновить связку
  (access: user_id берётся из токена; service: user_id из тела).
- PUT    /users/link/{link_id}             — обновить свою связку (access).
- DELETE /users/link/{link_id}             — удалить свою связку (access).
- POST   /users/link/code                  — выпустить одноразовый код (access).
- POST   /users/link/code/consume          — обменять код на связку (service).

ВАЖНО: роутер подключается ДО ``users_router``, иначе ``GET /users/link``
перехватится как ``GET /users/{pk}``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from config.provider import settings_tg
from config.redis import settings_redis
from src import dependencies as deps
from src.context import system_context
from src.excpetions.auth import PermissionDeniedError
from src.excpetions.crud import NotFoundError, ValidationError
from src.middleware.auth import get_current_user
from src.middleware.mix_scheme import get_principal
from src.middleware.principal import Principal
from src.models.enums.provider import Provider
from src.models.user import User
from src.schemas import (
    LinkCodeConsumeRequest,
    LinkCodeResponse,
    UserLinkCreate,
    UserLinkRead,
    UserLinkUpdate,
)
from src.services.link_code_service import consume_link_code, issue_link_code
from src.services.user_link_service import UserLinkService

router = APIRouter(prefix="/users/link", tags=["users"])


# --------------------------------------------------------------------------- #
# Lookup (access + service)
# --------------------------------------------------------------------------- #

@router.get("", response_model=UserLinkRead)
async def get_user_link(
    provider: Provider = Query(..., examples=["telegram"]),
    external_id: str = Query(..., max_length=64, examples=["123456789"]),
    service: UserLinkService = Depends(deps.get_service(UserLinkService)),
    principal: Principal = Depends(get_principal),
):
    """Найти связку по провайдеру и внешнему id.

    - сервисный токен — возвращает любую связку;
    - access-токен — только свою (иначе 404, чтобы не палить чужие данные).
    """
    link = await service.get_by_external(provider, external_id)
    if link is None:
        raise NotFoundError("Привязка не найдена")

    if principal.is_user:
        if principal.user is None or link.user_id != principal.user.user_id:
            raise NotFoundError("Привязка не найдена")

    return link


# --------------------------------------------------------------------------- #
# CRUD для ЛК (только access)
# --------------------------------------------------------------------------- #

@router.get("/all", response_model=list[UserLinkRead])
async def list_my_links(
    limit: int = 100,
    offset: int = 0,
    service: UserLinkService = Depends(deps.get_service(UserLinkService)),
    user: User = Depends(get_current_user),
):
    """Список привязок текущего пользователя."""
    return await service.list_for_user(user.user_id, limit=limit, offset=offset)


@router.get("/{link_id}", response_model=UserLinkRead)
async def get_my_link(
    link_id: int,
    service: UserLinkService = Depends(deps.get_service(UserLinkService)),
    user: User = Depends(get_current_user),
):
    """Получить свою привязку по id."""
    item = await service.get_for_user(link_id, user.user_id)
    if item is None:
        raise NotFoundError("Привязка не найдена")
    return item


@router.post("", response_model=UserLinkRead, status_code=201)
async def create_user_link(
    payload: UserLinkCreate,
    service: UserLinkService = Depends(deps.get_service(UserLinkService)),
    user: User = Depends(get_current_user),
):
    """Привязать аккаунт к текущему пользователю (только access-токен).

    ``user_id`` всегда берётся из токена; передавать чужой ``user_id`` нельзя.
    """
    if payload.user_id is not None and payload.user_id != user.user_id:
        raise PermissionDeniedError("Нельзя привязать аккаунт другому пользователю")

    data = UserLinkCreate(
        user_id=user.user_id,
        provider=payload.provider,
        external_id=payload.external_id,
        options=payload.options,
    )
    return await service.link_external(data)


@router.put("/{link_id}", response_model=UserLinkRead)
async def update_my_link(
    link_id: int,
    payload: UserLinkUpdate,
    service: UserLinkService = Depends(deps.get_service(UserLinkService)),
    user: User = Depends(get_current_user),
):
    """Обновить привязку текущего пользователя."""
    item = await service.update_for_user(link_id, user.user_id, payload)
    if item is None:
        raise NotFoundError("Привязка не найдена")
    return item


@router.delete("/{link_id}", status_code=204)
async def delete_my_link(
    link_id: int,
    service: UserLinkService = Depends(deps.get_service(UserLinkService)),
    user: User = Depends(get_current_user),
):
    """Удалить привязку текущего пользователя."""
    deleted = await service.delete_for_user(link_id, user.user_id)
    if not deleted:
        raise NotFoundError("Привязка не найдена")
    return None


# --------------------------------------------------------------------------- #
# Одноразовые коды для /start
# --------------------------------------------------------------------------- #

@router.post("/code", response_model=LinkCodeResponse, status_code=201)
async def create_link_code(
    provider: Provider = Query(default=Provider.TELEGRAM),
    user: User = Depends(get_current_user),
):
    """Выпустить короткоживущий одноразовый код для привязки в боте."""
    code = await issue_link_code(user.user_id, provider)

    deep_link = None
    username = settings_tg.TG_BOT_USERNAME.lstrip("@")
    if username:
        deep_link = f"https://t.me/{username}?start={code}"

    return LinkCodeResponse(
        code=code,
        expires_in=settings_redis.LINK_CODE_TTL_SEC,
        deep_link=deep_link,
    )


@router.post("/code/consume", response_model=UserLinkRead)
async def consume_link_code_endpoint(
    payload: LinkCodeConsumeRequest,
    service: UserLinkService = Depends(deps.get_service(UserLinkService)),
    principal: Principal = Depends(get_principal),
):
    """Обменять одноразовый код на привязку. Вызывает сервис-бот."""
    if not principal.is_service:
        raise PermissionDeniedError("Обмен кода доступен только сервисам")

    user_id = await consume_link_code(payload.code, payload.provider)
    if user_id is None:
        raise ValidationError("Код недействителен или истёк")

    data = UserLinkCreate(
        user_id=user_id,
        provider=payload.provider,
        external_id=payload.external_id,
        options=payload.options,
    )
    with system_context():
        return await service.link_external(data)
