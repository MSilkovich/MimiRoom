"""Handlers инструментов LLM.

Каждый handler — асинхронная функция, которую вызывает LLMService.
Handlers НЕ делают HTTP-запросы напрямую — они вызывают репозитории.
"""

from typing import Any

from src.logging import get_logger
from src.repositories import backend_repository

logger = get_logger(__name__)


async def get_services(
    user_id: int,
    limit: int = 100,
    offset: int = 0,
    **_: Any,
) -> list[dict[str, Any]]:
    """Вернуть список доступных услуг с ценами.

    Args:
        user_id: ID пользователя (передаётся из LLMService).
        limit: Сколько услуг вернуть.
        offset: Смещение от начала.

    Returns:
        Список ServiceRead.
    """
    logger.info("Tool get_services called: limit=%s offset=%s", limit, offset)
    return await backend_repository.get_services(limit=limit, offset=offset)


async def create_booking(
    user_id: int,
    date: str,
    time: str,
    services: list[dict[str, Any]],
    pet_id: int | None = None,
    master_id: int | None = None,
    comment: str | None = None,
    options: dict[str, Any] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Создать запись на услугу.

    Args:
        user_id: ID пользователя (передаётся из LLMService). 0 — анонимный гость.
        date: Дата в формате YYYY-MM-DD.
        time: Время в формате HH:MM:SS.
        services: Список услуг [{"service_id": int, "master_id": int | None}, ...].
        pet_id: ID питомца (если известен).
        master_id: ID мастера (если применимо ко всем услугам).
        comment: Комментарий к записи.
        options: Доп. информация, которой нет в полях (имя, телефон, пожелания...).

    Returns:
        BookRead — созданная запись.
    """
    logger.info(
        "Tool create_booking called: date=%s time=%s services=%s user_id=%s",
        date, time, services, user_id,
    )

    body: dict[str, Any] = {
        "date": date,
        "time": time,
        "source": "bot",
        "services": services,
    }

    # Для привязанного пользователя сохраняем владельца записи.
    # user_id=0 — анонимный гость TG-бота, client_id в core должен остаться NULL.
    if user_id and user_id > 0:
        body["client_id"] = user_id

    if pet_id is not None:
        body["pet_id"] = pet_id
    if master_id is not None:
        body["master_id"] = master_id
    if comment is not None:
        body["comment"] = comment
    if options:
        body["options"] = options

    result = await backend_repository.create_booking(body)
    logger.info("Booking created: book_id=%s", result.get("book_id"))
    return result
