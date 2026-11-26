"""Репозиторий для работы с услугами, слотами и бронированиями backend API.

Модель записи (расчётные слоты; мастер = user):
1. ``get_services``      — каталог услуг (с длительностью, буферами и мастерами);
2. ``get_service``       — одна услуга из каталога (для выбора мастера);
3. ``get_availability``  — свободные слоты по услуге/мастеру/периоду (POST, тело);
4. ``create_booking``    — создание брони по ``master_id`` + ``service_id`` + ``start_time``;
5. ``get_user_summary``  — сводка о пользователе.
"""

from typing import Any

from src.exceptions import BackendNotFoundError
from src.logging import get_logger
from src.schemas import Summary

from .base import BaseRepository

logger = get_logger(__name__)

API_PREFIX = "/api/v0.0.1"


class BackendRepository(BaseRepository):
    """Работа с услугами, слотами и бронированиями."""

    async def get_services(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Вернуть список услуг.

        Каждый элемент — ``ServiceRead``: ``service_id``, ``title``,
        ``price``, ``duration_minutes``, буферы и ``masters`` (мастера,
        которые услугу оказывают).
        """
        return await self._request(
            "GET",
            f"{API_PREFIX}/s/services",
            params={"limit": limit, "offset": offset},
        )

    async def get_service(self, service_id: int) -> dict[str, Any] | None:
        """Найти услугу в каталоге по id (через сервисный список услуг)."""
        services = await self.get_services(limit=500, offset=0)
        for service in services or []:
            if service.get("service_id") == service_id:
                return service
        return None

    async def get_masters(
        self, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Вернуть список мастеров (с их услугами) через сервисный доступ."""
        return await self._request(
            "GET",
            f"{API_PREFIX}/s/masters",
            params={"limit": limit, "offset": offset},
        )

    async def get_bookings(
        self,
        client_id: int | None = None,
        master_id: int | None = None,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Вернуть бронирования (фильтры: client_id, master_id, status)."""
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if client_id is not None:
            params["client_id"] = client_id
        if master_id is not None:
            params["master_id"] = master_id
        if status is not None:
            params["status"] = status
        return await self._request(
            "GET",
            f"{API_PREFIX}/bookings",
            params=params,
        )

    async def get_availability(
        self,
        service_id: int,
        date_from: str,
        date_to: str | None = None,
        master_id: int | None = None,
        pet_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """Вернуть свободные слоты по услуге на период.

        Вызывает ``POST /slots/available`` к backend API: параметры передаются
        в теле запроса (не в query). Слоты рассчитываются на сервере на лету;
        если ``master_id`` не задан — конкретного мастера подбирает backend.

        Args:
            service_id: id услуги.
            date_from: дата начала ``YYYY-MM-DD``.
            date_to: дата окончания ``YYYY-MM-DD`` (включительно); по умолчанию
                = ``date_from``.
            master_id: user_id мастера, если пользователь его выбрал.
            pet_id: id питомца (задел под расчёт длительности/цены).

        Returns:
            Список ``{master_id, service_id, start_time, end_time, available}``.
        """
        payload: dict[str, Any] = {
            "service_id": service_id,
            "date_from": date_from,
            "date_to": date_to or date_from,
        }
        if master_id is not None:
            payload["master_id"] = master_id
        if pet_id is not None:
            payload["pet_id"] = pet_id

        return await self._request(
            "POST",
            f"{API_PREFIX}/slots/available",
            json=payload,
        )

    async def create_booking(
        self,
        master_id: int,
        service_id: int,
        start_time: str,
        client_name: str | None = None,
        client_phone: str | None = None,
        client_id: int | None = None,
        pet_id: int | None = None,
        comment: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Создать бронь на конкретное время.

        Время (``start_time``) берётся из ответа ``get_availability``; сервер
        сам валидирует график, сетку слотов и пересечения (с учётом буферов).

        Клиент может быть авторизованным (``client_id``) либо гостем
        (``client_name`` + ``client_phone``).

        Returns:
            ``BookingRead`` в виде dict.
        """
        payload: dict[str, Any] = {
            "master_id": master_id,
            "service_id": service_id,
            "start_time": start_time,
        }
        if client_id is not None:
            payload["client_id"] = client_id
        if client_name:
            payload["client_name"] = client_name
        if client_phone:
            payload["client_phone"] = client_phone
        if pet_id is not None:
            payload["pet_id"] = pet_id
        if comment:
            payload["comment"] = comment
        if options:
            payload["options"] = options

        return await self._request(
            "POST",
            f"{API_PREFIX}/bookings",
            json=payload,
        )

    async def get_user_summary(self, user_id: int) -> Summary | None:
        """Получить сводку о пользователе.

        Args:
            user_id: int.

        Returns:
            Summary или None, если пользователь не найден.
        """
        try:
            payload = await self._request(
                "GET",
                f"{API_PREFIX}/users/{user_id}/summary",
            )
        except BackendNotFoundError:
            logger.info("User summary not found: user_id=%s", user_id)
            return None

        if not payload:
            return None
        return Summary.model_validate(payload)
