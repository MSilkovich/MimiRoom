"""CRUD для записи.

Путь: /book*
- GET    /book                   — список с пагинацией
- GET    /book/{id}              — одна книга
- POST   /book                   — создать
- PUT    /book/{id}              — обновить
- DELETE /book/{id}              — удалить

Ручки из этого роутера предусмотрены как для пользователй напрямую, так и для сервисов - поэтому нюансы с проверками в каждом методе(((
"""

from fastapi import APIRouter, Depends, Security

from src.context import system_context
from src.excpetions.crud import NotFoundError
from src.services import BookServiceService
from src import dependencies as deps
from src.schemas import BookCreate, BookRead, BookUpdate
from src.middleware.mix_scheme import get_principal
from src.middleware.principal import Principal

router = APIRouter(prefix="/book", tags=["book"])


@router.get("", response_model=list[BookRead])
async def book_list(
    limit: int = 100, offset: int = 0, servive: BookServiceService = Depends(deps.get_service(BookServiceService)),
    principal: Principal = Depends(get_principal)
):
    """Показать список записей."""
    # TODO: если principal.is_user то прокидываем rule для выборки по правам. и так везде
    return await servive.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=BookRead)
async def book_read(
    pk: int, servive: BookServiceService = Depends(deps.get_service(BookServiceService)),
    principal: Principal = Depends(get_principal)
):
    """Показать одну запись по id."""
    item = await servive.get(pk)
    if item is None:
        raise NotFoundError("Запись не найдена")
    return item


@router.post("", response_model=BookRead, status_code=201)
async def book_create(
    data: BookCreate, servive: BookServiceService = Depends(deps.get_service(BookServiceService)),
    principal: Principal = Depends(get_principal)
):
    """Создать запись."""
    if principal.is_service:
        # можно указать fake_user_id если потребуется, сейчас от имени системы
        with system_context():
            return await servive.create(data)
    else:
        # проврека прав доступа если надо
        return await servive.create(data)


@router.put("/{pk}", response_model=BookRead)
async def book_update(
    pk: int, data: BookUpdate, servive: BookServiceService = Depends(deps.get_service(BookServiceService)),
    principal: Principal = Depends(get_principal)
):
    """Обновить запись."""
    item = None
    if principal.is_service:
        # можно указать fake_user_id если потребуется, сейчас от имени системы
        with system_context():
            item = await servive.update(pk, data)
    else:
        # проврека прав доступа если надо
        item = await servive.update(pk, data)
    if item is None:
        raise NotFoundError("Запись не найдена")
    return item


@router.delete("/{pk}", status_code=204)
async def book_delete(
        pk: int, servive: BookServiceService = Depends(deps.get_service(BookServiceService)),
        principal: Principal = Depends(get_principal)):
    """Удалить запись."""
    if principal.is_service:
        # можно указать fake_user_id если потребуется, сейчас от имени системы
        with system_context():
            await servive.delete(pk)
    else:
        # проврека прав доступа если надо
        await servive.delete(pk)
