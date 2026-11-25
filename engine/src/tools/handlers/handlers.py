"""Handlers инструментов LLM.

Общие правила:
- источник данных — только core (каталог `/s/services`, `/s/masters`, слоты, брони);
- выводы компактные и в едином формате;
- ссылки на услугу/мастера принимаются как id ИЛИ название и разрешаются
  детерминированно (см. ``resolvers``); при неоднозначности возвращаем
  ``ambiguous`` и НЕ угадываем.
"""

from datetime import datetime, timezone
from typing import Any

from src.logging import get_logger
from src.repositories import backend_repository
from src.tools import catalog as catalog_mod
from src.tools import resolvers

logger = get_logger(__name__)

DEFAULT_SLOTS_LIMIT = 12


async def _get_catalog() -> dict[str, Any]:
    try:
        return await catalog_mod.get_catalog()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Catalog unavailable")
        raise ValueError(f"Каталог услуг временно недоступен: {exc}") from exc


def _candidate_brief(card: dict[str, Any]) -> dict[str, Any]:
    if "service_id" in card:
        return {
            "service_id": card.get("service_id"),
            "title": card.get("title"),
            "price": card.get("price"),
            "duration_minutes": card.get("duration_minutes"),
            "breed": card.get("breed"),
            "score": card.get("score"),
        }
    return {
        "user_id": card.get("user_id"),
        "name": card.get("name"),
        "services": card.get("services"),
        "score": card.get("score"),
    }


def _resolve_error(field: str, result: dict[str, Any]) -> dict[str, Any]:
    status = result.get("status")
    code = f"ambiguous_{field}" if status == "ambiguous" else f"{field}_not_found"
    return {
        "error": code,
        "message": (
            "Несколько вариантов — уточните у пользователя."
            if status == "ambiguous"
            else "Ничего не найдено — уточните у пользователя."
        ),
        "candidates": [
            _candidate_brief(card) for card in result.get("candidates", [])
        ],
    }


def _service_brief(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "service_id": card.get("service_id"),
        "title": card.get("title"),
        "price": card.get("price"),
        "duration_minutes": card.get("duration_minutes"),
    }


# ---------------------------------------------------------------------------
# Инструменты
# ---------------------------------------------------------------------------

async def get_services(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    **_: Any,
) -> list[dict[str, Any]]:
    """Каталог услуг (компактные карточки с id, ценой, длительностью, мастерами)."""
    logger.info("Tool get_services called: limit=%s offset=%s", limit, offset)
    catalog = await _get_catalog()
    services = catalog.get("services", [])
    return services[offset: offset + limit]


async def find_service(
    user_id: int,
    query: str,
    limit: int = 5,
    **_: Any,
) -> dict[str, Any]:
    """Нечёткий поиск услуги по фразе пользователя (учитывает опечатки).

    Если ничего не найдено — возвращает ``fallback`` (общая услуга, напр.
    комплексный груминг), чтобы модель могла предложить её пользователю.
    """
    logger.info("Tool find_service called: query=%r", query)
    catalog = await _get_catalog()
    matches = catalog_mod.find_services(query, catalog, limit=limit)
    fallback = None if matches else catalog_mod.find_default_service(catalog)
    return {"query": query, "matches": matches, "fallback": fallback}


async def get_masters(
    user_id: int,
    service: Any | None = None,
    limit: int = 100,
    **_: Any,
) -> dict[str, Any]:
    """Список мастеров (и их услуг); можно отфильтровать по услуге."""
    logger.info("Tool get_masters called: service=%r", service)
    catalog = await _get_catalog()
    masters = catalog.get("masters", [])

    if service is not None:
        resolved = resolvers.resolve_service(service, catalog)
        if resolved["status"] != "ok":
            return _resolve_error("service", resolved)
        service_id = resolved["service"]["service_id"]
        masters = [
            master
            for master in masters
            if any(
                item.get("service_id") == service_id
                for item in master.get("services", [])
            )
        ]

    return {"masters": masters[:limit]}


async def get_availability(
    user_id: int,
    service: Any,
    date_from: str,
    master: Any | None = None,
    date_to: str | None = None,
    limit: int = DEFAULT_SLOTS_LIMIT,
    **_: Any,
) -> dict[str, Any]:
    """Свободные слоты под услугу/мастера на период (расчётные)."""
    logger.info(
        "Tool get_availability called: service=%r master=%r date=%s..%s",
        service, master, date_from, date_to,
    )
    catalog = await _get_catalog()

    resolved_service = resolvers.resolve_service(service, catalog)
    if resolved_service["status"] != "ok":
        return _resolve_error("service", resolved_service)
    service_card = resolved_service["service"]

    master_id = None
    if master is not None:
        resolved_master = resolvers.resolve_master(
            master, catalog, service_id=service_card["service_id"]
        )
        if resolved_master["status"] != "ok":
            return _resolve_error("master", resolved_master)
        master_id = resolved_master["master"]["user_id"]

    date_to = date_to or date_from
    items = await backend_repository.get_availability(
        service_id=service_card["service_id"],
        date_from=date_from,
        date_to=date_to,
        master_id=master_id,
    )

    _, masters_map = catalog_mod.catalog_maps(catalog)
    slots: list[dict[str, Any]] = []
    for slot in items or []:
        slot_master_id = slot.get("master_id")
        master_card = masters_map.get(slot_master_id)
        slots.append(
            {
                "master_id": slot_master_id,
                "master_name": (
                    master_card["name"]
                    if master_card
                    else str(slot_master_id)
                ),
                "service_id": slot.get("service_id", service_card["service_id"]),
                "start_time": slot.get("start_time"),
                "end_time": slot.get("end_time"),
            }
        )

    slots.sort(key=lambda item: item.get("start_time") or "")
    return {
        "service": _service_brief(service_card),
        "date_from": date_from,
        "date_to": date_to,
        "total": len(slots),
        "slots": slots[:limit],
    }


async def create_booking(
    user_id: int,
    service: Any,
    master: Any,
    start_time: str,
    client_name: str | None = None,
    client_phone: str | None = None,
    client_id: int | None = None,
    pet_id: int | None = None,
    comment: str | None = None,
    options: dict[str, Any] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Создать бронь на конкретное время (service/master — id или название)."""
    logger.info(
        "Tool create_booking called: service=%r master=%r start=%s client=%s",
        service, master, start_time, client_name or client_id,
    )
    catalog = await _get_catalog()

    resolved_service = resolvers.resolve_service(service, catalog)
    if resolved_service["status"] != "ok":
        return _resolve_error("service", resolved_service)
    service_card = resolved_service["service"]

    resolved_master = resolvers.resolve_master(
        master, catalog, service_id=service_card["service_id"]
    )
    if resolved_master["status"] != "ok":
        return _resolve_error("master", resolved_master)
    master_card = resolved_master["master"]

    if client_id is None and user_id and user_id > 0:
        client_id = user_id

    result = await backend_repository.create_booking(
        master_id=master_card["user_id"],
        service_id=service_card["service_id"],
        start_time=start_time,
        client_name=client_name,
        client_phone=client_phone,
        client_id=client_id,
        pet_id=pet_id,
        comment=comment,
        options=options,
    )
    logger.info("Booking created: %s", (result or {}).get("booking_id"))

    return {
        "booking_id": (result or {}).get("booking_id"),
        "service_id": service_card["service_id"],
        "service_title": service_card["title"],
        "master_id": master_card["user_id"],
        "master_name": master_card["name"],
        "start_time": (result or {}).get("start_time", start_time),
        "end_time": (result or {}).get("end_time"),
        "status": (result or {}).get("status"),
    }


async def get_my_appointments(
    user_id: int,
    include_past: bool = False,
    limit: int = 10,
    **_: Any,
) -> dict[str, Any]:
    """Записи клиента: ближайшие активные (или все при include_past)."""
    logger.info("Tool get_my_appointments called: user_id=%s", user_id)
    if not user_id or user_id <= 0:
        return {"authorized": False, "appointments": []}

    catalog = await _get_catalog()
    services_map, masters_map = catalog_mod.catalog_maps(catalog)
    bookings = await backend_repository.get_bookings(
        client_id=user_id, limit=100
    )

    now = datetime.now(timezone.utc)
    appointments: list[dict[str, Any]] = []
    for booking in bookings or []:
        status = booking.get("status")
        start_time = booking.get("start_time")
        if not include_past:
            if status not in ("pending", "confirmed"):
                continue
            try:
                moment = datetime.fromisoformat(start_time)
                if moment.tzinfo is None:
                    moment = moment.replace(tzinfo=timezone.utc)
                if moment < now:
                    continue
            except (TypeError, ValueError):
                pass

        service_id = booking.get("service_id")
        master_id = booking.get("master_id")
        appointments.append(
            {
                "booking_id": booking.get("booking_id"),
                "service_id": service_id,
                "service_title": (services_map.get(service_id) or {}).get(
                    "title"
                ),
                "master_id": master_id,
                "master_name": (masters_map.get(master_id) or {}).get("name"),
                "start_time": start_time,
                "end_time": booking.get("end_time"),
                "status": status,
            }
        )

    appointments.sort(key=lambda item: item.get("start_time") or "")
    return {"authorized": True, "appointments": appointments[:limit]}
