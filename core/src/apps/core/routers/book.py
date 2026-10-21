"""CRUD для записи.

Путь: /book*
- GET    /book                   — список с пагинацией
- GET    /book/{id}              — одна книга
- POST   /book                   — создать
- PUT    /book/{id}              — обновить
- DELETE /book/{id}              — удалить

Примечание: в нашем проекте «книга» — это запись вручную, а не счётчик.
"""

from fastapi import APIRouter, Depends, Security

from src.services import BookService
from src import dependencies as deps
from src.schemas import BookCreate, BookRead, BookUpdate
from src.middleware.auth import get_current_user, bearer_scheme

router = APIRouter(prefix="/book", tags=["book"], dependencies=[
    Security(bearer_scheme),
    Depends(get_current_user),
])


@router.get("", response_model=list[BookRead])
async def book_list(
    limit: int = 100, offset: int = 0, servive: BookService = Depends(deps.get_service(BookService))
):
    """Показать список книг (записей)."""
    return await servive.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=BookRead)
async def book_read(pk: int, servive: BookService = Depends(deps.get_service(BookService))):
    """Показать одну книгу по id."""
    item = await servive.get(pk)
    if item is None:
        raise deps.NotFoundError(detail="Книга не найдена")
    return item


@router.post("", response_model=BookRead, status_code=201)
async def book_create(data: BookCreate, servive: BookService = Depends(deps.get_service(BookService))):
    """Создать книгу (запись)."""
    return await servive.create(data)


@router.put("/{pk}", response_model=BookRead)
async def book_update(pk: int, data: BookUpdate, servive: BookService = Depends(deps.get_service(BookService))):
    """Обновить книгу."""
    item = await servive.update(pk, data)
    if item is None:
        raise deps.NotFoundError(detail="Книга не найдена")
    return item


@router.delete("/{pk}", status_code=204)
async def book_delete(pk: int, servive: BookService = Depends(deps.get_service(BookService))):
    """Удалить книгу."""
    await servive.delete(pk)
