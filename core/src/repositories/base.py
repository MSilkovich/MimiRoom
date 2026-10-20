from abc import ABC, abstractmethod
from typing import Optional


class AbstractRepository(ABC):

    @property
    @abstractmethod
    def pk_name(self) -> str:
        """Имя первичного ключа модели (например, user_id)."""
        raise NotImplementedError

    @abstractmethod
    async def create(self, data: dict):
        raise NotImplementedError

    @abstractmethod
    async def update(self, data: dict, **filters):
        raise NotImplementedError

    @abstractmethod
    async def delete(self, **filters) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_single(self, **filters) -> Optional[object] | None:
        raise NotImplementedError

    @abstractmethod
    async def get_multi(self, order: str | None = None, limit: int = 100, offset: int = 0):
        raise NotImplementedError

