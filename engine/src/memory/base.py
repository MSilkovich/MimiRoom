"""Абстракция хранилища истории диалога."""

from typing import Protocol

from src.schemas.llm import Role


class MemoryStore(Protocol):
    async def load(self, user_id: int, channel: str) -> list[dict]:
        """Вернуть историю сообщений (без system prompt)."""
        ...

    async def append(self, user_id: int, channel: str, message: dict) -> None:
        """Добавить одно сообщение в историю."""
        ...

    async def clear(self, user_id: int, channel: str) -> None:
        """Очистить историю (например, по /reset)."""
        ...
