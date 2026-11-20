"""No-op хранилище: история не сохраняется. Замена на Redis — позже."""

from .base import MemoryStore


class NoopMemoryStore(MemoryStore):
    async def load(self, user_id: int, channel: str) -> list[dict]:
        return []

    async def append(self, user_id: int, channel: str, message: dict) -> None:
        return None

    async def clear(self, user_id: int, channel: str) -> None:
        return None
