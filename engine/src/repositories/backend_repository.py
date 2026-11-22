"""Репозиторий для работы с услугами, слотами и бронированиями backend API.

Новая модель записи (slot-based):
1. ``get_services``      — каталог услуг (с длительностью, буферами и мастерами);
2. ``get_service``       — одна услуга из каталога (для выбора мастера);
3. ``get_availability``  — свободные слоты мастера по услуге на период;
4. ``create_booking``    — создание брони по конкретному ``slot_id``;
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
        ``price``, ``duration_minutes``, буферы и ``resources`` (мастера,
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

    async def get_availability(
        self,
        resource_id: int,
        service_id: int,
        date_from: str,
        date_to: str,
        step_minutes: int | None = None,
        only_available: bool = True,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Вернуть слоты мастера по услуге на период.

        Args:
            resource_id: id мастера.
            service_id: id услуги.
            date_from: дата начала ``YYYY-MM-DD``.
            date_to: дата окончания ``YYYY-MM-DD`` (включительно).
            step_minutes: шаг сетки (необязательно).
            only_available: вернуть только свободные слоты.
            limit: максимум слотов.
        """
        params: dict[str, Any] = {
            "resource_id": resource_id,
            "service_id": service_id,
            "date_from": date_from,
            "date_to": date_to,
            "only_available": only_available,
            "limit": limit,
        }
        if step_minutes is not None:
            params["step_minutes"] = step_minutes

        return await self._request(
            "GET",
            f"{API_PREFIX}/slots/availability",
            params=params,
        )

    async def create_booking(
        self,
        slot_id: int,
        client_name: str,
        client_phone: str,
        comment: str | None = None,
    ) -> dict[str, Any]:
        """Создать бронь по слоту.

        Сервер сам переводит слот в ``booked`` и валидирует пересечения.

        Returns:
            ``BookingRead`` в виде dict (с вложенным ``slot``).
        """
        payload: dict[str, Any] = {
            "slot_id": slot_id,
            "client_name": client_name,
            "client_phone": client_phone,
        }
        if comment:
            payload["comment"] = comment

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
