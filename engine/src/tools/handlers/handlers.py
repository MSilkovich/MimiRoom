"""Handlers инструментов LLM.

Каждый handler — асинхронная функция, которую вызывает LLMService.
Handlers НЕ делают HTTP-запросы напрямую — они вызывают репозитории.
"""

from typing import Any

from src.logging import get_logger
from src.repositories import backend_repository

logger = get_logger(__name__)


def _master_name(master: dict[str, Any]) -> str:
    parts = [master.get("name"), master.get("surname")]
    return " ".join(part for part in parts if part) or str(master.get("user_id"))


async def get_services(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    **_: Any,
) -> list[dict[str, Any]]:
    """Вернуть список доступных услуг с ценами и мастерами.

    Args:
        user_id: ID пользователя (передаётся из LLMService).
        limit: Сколько услуг вернуть.
        offset: Смещение от начала.

    Returns:
        Список ServiceRead (включая ``duration_minutes`` и ``masters``).
    """
    logger.info("Tool get_services called: limit=%s offset=%s", limit, offset)
    return await backend_repository.get_services(limit=limit, offset=offset)


async def get_availability(
    user_id: int,
    service_id: int,
    date_from: str,
    date_to: str | None = None,
    master_id: int | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Вернуть реальные свободные слоты под услугу на период.

    Слоты рассчитываются на сервере (график мастера + длительность/буферы
    услуги + существующие брони). Если ``master_id`` не задан — конкретного
    мастера подбирает backend. LLM обязан выбирать время для брони только из
    ответа этого инструмента.

    Args:
        user_id: ID пользователя.
        service_id: id услуги из get_services.
        date_from: дата начала ``YYYY-MM-DD``.
        date_to: дата окончания (включительно), по умолчанию = date_from.
        master_id: user_id мастера, если пользователь его выбрал.

    Returns:
        dict: ``service``, ``date_from``, ``date_to`` и список ``slots``.
    """
    logger.info(
        "Tool get_availability called: service_id=%s date=%s..%s master_id=%s",
        service_id, date_from, date_to, master_id,
    )

    service = await backend_repository.get_service(service_id)
    if service is None:
        raise ValueError(f"Услуга {service_id} не найдена")

    date_to = date_to or date_from
    items = await backend_repository.get_availability(
        service_id=service_id,
        date_from=date_from,
        date_to=date_to,
        master_id=master_id,
    )

    masters_by_id = {
        master.get("user_id"): master
        for master in (service.get("masters") or [])
    }

    slots: list[dict[str, Any]] = []
    for slot in items or []:
        slot_master_id = slot.get("master_id")
        master = masters_by_id.get(slot_master_id) or {
            "user_id": slot_master_id
        }
        slots.append(
            {
                "master_id": slot_master_id,
                "master_name": _master_name(master),
                "service_id": slot.get("service_id", service_id),
                "start_time": slot.get("start_time"),
                "end_time": slot.get("end_time"),
            }
        )

    slots.sort(key=lambda item: item.get("start_time") or "")

    return {
        "service": {
            "service_id": service.get("service_id"),
            "title": service.get("title"),
            "price": service.get("price"),
            "duration_minutes": service.get("duration_minutes"),
        },
        "date_from": date_from,
        "date_to": date_to,
        "slots": slots,
    }


async def create_booking(
    user_id: int,
    master_id: int,
    service_id: int,
    start_time: str,
    client_name: str | None = None,
    client_phone: str | None = None,
    client_id: int | None = None,
    pet_id: int | None = None,
    comment: str | None = None,
    options: dict[str, Any] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Создать бронь на конкретное время.

    Args:
        user_id: ID пользователя. 0 — анонимный гость.
        master_id: user_id мастера из выбранного слота get_availability.
        service_id: id услуги.
        start_time: конкретное время начала из get_availability (ISO 8601).
        client_name: имя клиента (для гостя обязательно).
        client_phone: телефон клиента (для гостя обязателен).
        client_id: id авторизованного клиента (если известен).
        pet_id: id питомца из сводки (если пользователь его назвал).
        comment: комментарий/пожелания.
        options: произвольные доп. данные.

    Returns:
        BookingRead — созданная бронь.
    """
    logger.info(
        "Tool create_booking called: master_id=%s service_id=%s start=%s "
        "client=%s user_id=%s",
        master_id, service_id, start_time, client_name or client_id, user_id,
    )

    # Авторизованного пользователя связываем с бронью (если не передан явно).
    if client_id is None and user_id and user_id > 0:
        client_id = user_id

    result = await backend_repository.create_booking(
        master_id=master_id,
        service_id=service_id,
        start_time=start_time,
        client_name=client_name,
        client_phone=client_phone,
        client_id=client_id,
        pet_id=pet_id,
        comment=comment,
        options=options,
    )
    logger.info("Booking created: booking_id=%s", (result or {}).get("booking_id"))
    return result
