from abc import ABC, abstractmethod
from typing import Optional

from src.permissions.permission_rule import PermissionRule


class AbstractRepository(ABC):

    @property
    @abstractmethod
    def pk_name(self) -> str:
        """Имя первичного ключа модели (например, user_id)."""
        raise NotImplementedError

    @abstractmethod
    async def create(self, data: dict, rule: PermissionRule | None = None):
        raise NotImplementedError

    @abstractmethod
    async def update(self, data: dict, rule: PermissionRule | None = None, **filters):
        raise NotImplementedError

    @abstractmethod
    async def delete(self, rule: PermissionRule | None = None, **filters) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_single(self, rule: PermissionRule | None = None, **filters) -> Optional[object] | None:
        raise NotImplementedError

    @abstractmethod
    async def get_multi(self, order: str | None = None, limit: int = 100, offset: int = 0, rule: PermissionRule | None = None, **filters) -> list[object]:
        raise NotImplementedError
