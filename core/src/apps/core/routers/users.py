"""CRUD для пользователей (User).

Путь: /users*
- GET    /users                          — список пользователей
- GET    /users/{id}                     — один пользователь
- POST   /users                          — создать пользователя
- PUT    /users/{id}                     — обновить пользователя
- DELETE /users/{id}                     — удалить пользователя
TODO: дополнить для link
"""

from fastapi import APIRouter, Depends, Security

from src import dependencies as deps
from src.excpetions.crud import NotFoundError
from src.middleware.mix_scheme import get_principal
from src.middleware.principal import Principal
from src.schemas.user import UserCreate, UserRead, UserUpdate
from src.schemas import Summary, UserSummary
from src.services.user_service import UserService
from src.middleware.auth import get_current_user, auth_bearer_scheme

router = APIRouter(prefix="/users", tags=["users"], dependencies=[
    Security(auth_bearer_scheme),
    Depends(get_current_user),
])


@router.get("", response_model=list[UserRead])
async def user_list(
    limit: int = 100, offset: int = 0, service: UserService = Depends(deps.get_service(UserService))
):
    """Показать список пользователей."""
    return await service.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=UserRead)
async def user_read(pk: int, service: UserService = Depends(deps.get_service(UserService))):
    """Показать одного пользователя по id."""
    user = await service.get(pk)
    if user is None:
        raise NotFoundError("Пользователь не найден")
    return user


@router.post("", response_model=UserRead)
async def user_create(
    payload: UserCreate,
    service: UserService = Depends(deps.get_service(UserService))
):
    """
    Создать пользователя.
    По умолчанию - CLIENT.
    """
    return await service.create(payload)


@router.put("/{pk}", response_model=UserRead)
async def user_update(
    pk: int,
    payload: UserUpdate,
    service: UserService = Depends(deps.get_service(UserService))
):
    """Обновить пользователя."""
    user = await service.update(pk, payload)
    if user is None:
        raise NotFoundError("Пользователь не найден")
    return user


@router.delete("/{pk}", status_code=204)
async def user_delete(pk: int, service: UserService = Depends(deps.get_service(UserService))):
    """Удалить пользователя."""
    await service.delete(pk)


# region service

# Роутер без пользовательских зависимостей: сюда пускаем и клиента
# (access-токен), и сервис (service-токен) через ``get_principal``.
router_service = APIRouter(prefix="/users", tags=["users"])


@router_service.get("/{pk}/summary", response_model=Summary)
async def user_summary(
    pk: int, service: UserService = Depends(deps.get_service(UserService)),
    principal: Principal = Depends(get_principal)
):
    """Сводка пользователя (доступна клиенту и сервису).

    Для ``pk == 0`` возвращаем «гостевую» сводку: engine использует
    user_id=0 для неавторизованных пользователей TG-бота и не должен
    падать на отсутствующем пользователе.
    """
    summary = await service.get_summary_by_id(pk)
    if summary is None:
        if pk == 0:
            return Summary(
                user=UserSummary(id=0, name="Гость", phone=None),
                pets=[],
                notes=None,
            )
        raise NotFoundError("Пользователь не найден")
    return summary

# endregion
