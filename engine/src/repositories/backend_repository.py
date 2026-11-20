"""Репозиторий для работы с бронированиями backend API.

Методы:
- get_services  — список услуг с ценами
- create_booking — создание записи
- get_user_summary - сводка по пользователю
"""

from typing import Any

from src.schemas import Summary

from .base import BaseRepository


class BackendRepository(BaseRepository):
    """Работа с услугами и бронированиями."""

    async def get_services(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Вернуть список услуг.

        Args:
            limit: Сколько услуг вернуть (по умолчанию 100).
            offset: Смещение от начала списка.

        Returns:
            Список ServiceRead в виде dict'ов.
        """
        return await self._request(
            "GET",
            "/api/v0.0.1/s/services",
            params={"limit": limit, "offset": offset},
        )

    async def create_booking(self, data: dict[str, Any]) -> dict[str, Any]:
        """Создать запись (бронь).

        Args:
            data: BookCreate согласно спецификации backend'а.

        Returns:
            BookRead в виде dict.
        """
        return await self._request(
            "POST",
            "/api/v0.0.1/book",
            json=data,
        )

    async def get_user_summary(self, user_id: int) -> Summary | None:
        """Получить сводку о пользователе.

        Args:
            user_id: int.

        Returns:
            Summary или None, если пользователь не найден.
        """
        json = await self._request(
            "GET",
            f"/api/v0.0.1/users/{user_id}/summary"
        )
        return Summary(**json)
