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
from src.schemas.user import UserCreate, UserRead, UserUpdate
from src.schemas.user_link import UserLinkCreate, UserLinkRead, UserLinkUpdate
from src.services.user_service import UserService
from src.services.user_link_service import UserLinkService
from src.middleware.auth import get_current_user, bearer_scheme

router = APIRouter(prefix="/users", tags=["users"], dependencies=[
    Security(bearer_scheme),
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
    """Создать пользователя.

    Текущий ``current_user`` нужен, чтобы ``who_create``/``who_update`` были
    заполнены из контекста. Пароль при выдаче не эскейпится в ``UserRead``.
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


# region link


@router.post("/link", response_model=UserLinkRead)
async def link_messanger(
    payload: UserLinkCreate,
    service: UserLinkService = Depends(deps.get_service(UserLinkService))
):
    """Привязать соц. сеть пользователя."""
    return await service.create(payload)
