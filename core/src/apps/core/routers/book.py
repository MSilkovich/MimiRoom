"""CRUD для записи.

Путь: /book*
- GET    /book                   — список с пагинацией
- GET    /book/{id}              — одна книга
- POST   /book                   — создать
- PUT    /book/{id}              — обновить
- DELETE /book/{id}              — удалить

Примечание: в нашем проекте «книга» — это запись вручную, а не счётчик.
"""

from fastapi import APIRouter, Depends

from src.services import BookService
from src import dependencies as deps
from src.schemas import BookCreate, BookRead, BookUpdate

router = APIRouter("/book", tags=["book"])


@router.get("", response_model=list[BookRead])
async def book_list(
    limit: int = 100, offset: int = 0, uow: BookService = Depends(deps.get_uow_factory)
):
    """Показать список книг (записей)."""
    return await uow.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=BookRead)
async def book_read(pk: int, uow: BookService = Depends(deps.get_uow_factory)):
    """Показать одну книгу по id."""
    item = await uow.get(pk)
    if item is None:
        raise deps.NotFoundError(detail="Книга не найдена")
    return item


@router.post("", response_model=BookRead, status_code=201)
async def book_create(data: BookCreate, uow: BookService = Depends(deps.get_uow_factory)):
    """Создать книгу (запись)."""
    return await uow.create(data)


@router.put("/{pk}", response_model=BookRead)
async def book_update(pk: int, data: BookUpdate, uow: BookService = Depends(deps.get_uow_factory)):
    """Обновить книгу."""
    item = await uow.update(pk, data)
    if item is None:
        raise deps.NotFoundError(detail="Книга не найдена")
    return item


@router.delete("/{pk}", status_code=204)
async def book_delete(pk: int, uow: BookService = Depends(deps.get_uow_factory)):
    """Удалить книгу."""
    await uow.delete(pk)
